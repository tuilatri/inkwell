from __future__ import annotations

import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import get_current_user, require_csrf
from app.core.security import (
    REFRESH_COOKIE,
    clear_auth_cookies,
    create_token,
    decode_token,
    set_auth_cookies,
    verify_password,
    hash_password,
)
from app.db.models import AdminUser, TokenSession
from app.db.session import get_db
from app.schemas import ChangePasswordRequest, LoginRequest, MeOut

router = APIRouter(prefix="/api/auth", tags=["auth"])

_FAILED: dict[str, tuple[int, float]] = {}
_MAX_FAILURES = 5
_COOLDOWN_SECONDS = 60.0


def _client_key(username: str, request: Request) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{username}|{host}"


def _check_rate_limit(key: str) -> None:
    count, until = _FAILED.get(key, (0, 0.0))
    if until and time.monotonic() < until:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="too many attempts")
    if until and time.monotonic() >= until:
        _FAILED.pop(key, None)


def _record_failure(key: str) -> None:
    count, _ = _FAILED.get(key, (0, 0.0))
    count += 1
    _FAILED[key] = (count, time.monotonic() + _COOLDOWN_SECONDS if count >= _MAX_FAILURES else 0.0)


async def _issue_tokens(
    response: Response,
    user_id: int,
    session: AsyncSession,
    settings,
) -> None:
    access, access_jti, access_exp = create_token(
        user_id, "access", settings.secret_key,
        settings.access_token_ttl_minutes, settings.refresh_token_ttl_days,
    )
    refresh, refresh_jti, refresh_exp = create_token(
        user_id, "refresh", settings.secret_key,
        settings.access_token_ttl_minutes, settings.refresh_token_ttl_days,
    )
    session.add_all([
        TokenSession(jti=access_jti, user_id=user_id, kind="access", expires_at=access_exp),
        TokenSession(jti=refresh_jti, user_id=user_id, kind="refresh", expires_at=refresh_exp),
    ])
    await session.commit()
    set_auth_cookies(
        response, access, refresh,
        secure=settings.environment == "production",
        access_ttl_minutes=settings.access_token_ttl_minutes,
        refresh_ttl_days=settings.refresh_token_ttl_days,
    )


@router.post("/login", response_model=MeOut)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> MeOut:
    settings = get_settings()
    key = _client_key(payload.username, request)
    _check_rate_limit(key)
    user = (
        await session.execute(select(AdminUser).where(AdminUser.username == payload.username))
    ).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        _record_failure(key)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bad credentials")
    _FAILED.pop(key, None)
    await _issue_tokens(response, user.id, session, settings)
    return MeOut(id=user.id, username=user.username)


@router.post("/refresh", dependencies=[Depends(require_csrf)])
async def refresh(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    settings = get_settings()
    token = request.cookies.get(REFRESH_COOKIE, "")
    try:
        user_id, jti = decode_token(token, "refresh", settings.secret_key)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bad refresh token")
    row = await session.get(TokenSession, jti)
    if row is None or row.revoked_at is not None or row.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh expired")
    row.revoked_at = datetime.utcnow()
    await session.commit()
    await _issue_tokens(response, user_id, session, settings)
    return {"ok": True}


@router.post("/logout", dependencies=[Depends(require_csrf)])
async def logout(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    settings = get_settings()
    for name, kind in (("nr_access", "access"), (REFRESH_COOKIE, "refresh")):
        token = request.cookies.get(name, "")
        try:
            _, jti = decode_token(token, kind, settings.secret_key)
        except ValueError:
            continue
        row = await session.get(TokenSession, jti)
        if row is not None:
            row.revoked_at = datetime.utcnow()
    await session.commit()
    clear_auth_cookies(response)
    return {"ok": True}


@router.get("/me", response_model=MeOut)
async def me(user: AdminUser = Depends(get_current_user)) -> MeOut:
    return MeOut(id=user.id, username=user.username)


@router.post("/change-password", dependencies=[Depends(require_csrf)])
async def change_password(
    payload: ChangePasswordRequest,
    user: AdminUser = Depends(get_current_user),
    response: Response = None,
    session: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bad credentials")
    user.password_hash = hash_password(payload.new_password)
    await session.execute(
        update(TokenSession).where(TokenSession.user_id == user.id).values(revoked_at=datetime.utcnow())
    )
    await session.commit()
    if response is not None:
        clear_auth_cookies(response)
    return {"ok": True}
