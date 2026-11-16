from __future__ import annotations

from datetime import datetime

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import ACCESS_COOKIE, CSRF_HEADER, CSRF_VALUE, decode_token
from app.db.models import AdminUser, TokenSession
from app.db.session import get_db


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> AdminUser:
    token = request.cookies.get(ACCESS_COOKIE, "")
    settings = get_settings()
    try:
        user_id, jti = decode_token(token, "access", settings.secret_key)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated")
    token_row = await session.get(TokenSession, jti)
    if (
        token_row is None
        or token_row.kind != "access"
        or token_row.revoked_at is not None
        or token_row.expires_at <= datetime.utcnow()
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="session expired")
    user = await session.get(AdminUser, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated")
    return user


async def require_csrf(
    request: Request,
    x_requested_with: str | None = Header(default=None, alias=CSRF_HEADER),
) -> None:
    """State-changing requests must carry the SPA marker (SameSite is the other half)."""
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and x_requested_with != CSRF_VALUE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF check failed")


async def get_db_session(session: AsyncSession = Depends(get_db)) -> AsyncSession:
    return session
