from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Literal

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from fastapi import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AdminUser

_hasher = PasswordHasher()

ACCESS_COOKIE = "nr_access"
REFRESH_COOKIE = "nr_refresh"
CSRF_HEADER = "X-Requested-With"
CSRF_VALUE = "XMLHttpRequest"

TokenKind = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, password)
    except (VerifyMismatchError, VerificationError):
        return False


def create_token(
    user_id: int,
    kind: TokenKind,
    secret_key: str,
    ttl_minutes: int,
    ttl_days: int,
) -> tuple[str, str, datetime]:
    """Return (token, jti, expires_at-naive-utc)."""
    jti = uuid.uuid4().hex
    lifetime = timedelta(minutes=ttl_minutes) if kind == "access" else timedelta(days=ttl_days)
    expires_at = datetime.utcnow() + lifetime
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "kind": kind,
        "exp": expires_at,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, secret_key, algorithm="HS256"), jti, expires_at


def decode_token(token: str, expected_kind: TokenKind, secret_key: str) -> tuple[int, str]:
    """Return (user_id, jti). Raises ValueError on any invalid token."""
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise ValueError("invalid token") from exc
    if payload.get("kind") != expected_kind:
        raise ValueError("wrong token kind")
    try:
        return int(payload["sub"]), str(payload["jti"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid claims") from exc


def set_auth_cookies(
    response: Response,
    access: str,
    refresh: str,
    secure: bool = False,
    access_ttl_minutes: int = 20,
    refresh_ttl_days: int = 14,
) -> None:
    """Cookie lifetimes mirror the JWT expiries (settings, not hardcoded values)."""
    common = {"httponly": True, "samesite": "strict", "secure": secure, "path": "/"}
    response.set_cookie(ACCESS_COOKIE, access, max_age=access_ttl_minutes * 60, **common)
    response.set_cookie(REFRESH_COOKIE, refresh, max_age=refresh_ttl_days * 24 * 3600, **common)


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")


async def seed_admin_from_env(session: AsyncSession, username: str, password: str) -> bool:
    """Seed only when the table is empty. Returns True when a row was inserted."""
    existing = await session.execute(select(AdminUser).limit(1))
    if existing.scalar_one_or_none() is not None:
        return False
    session.add(AdminUser(username=username, password_hash=hash_password(password)))
    await session.commit()
    return True
