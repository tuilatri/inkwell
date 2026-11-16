from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password, seed_admin_from_env, verify_password
from app.db.models import AdminUser, TokenSession


async def test_seed_runs_once_only(db_session):
    assert await seed_admin_from_env(db_session, "admin", "admin-pass-123") is True
    row = (await db_session.execute(select(AdminUser))).scalar_one()
    original_hash = row.password_hash
    assert verify_password("admin-pass-123", original_hash)
    assert await seed_admin_from_env(db_session, "admin", "another-password") is False
    row = (await db_session.execute(select(AdminUser))).scalar_one()
    assert row.password_hash == original_hash
    assert not verify_password("another-password", row.password_hash)


async def test_change_password_voids_env_credentials(auth_client, db_session):
    response = await auth_client.post(
        "/api/auth/change-password",
        json={"current_password": "admin-pass-123", "new_password": "new-pass-456"},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert response.status_code == 200, response.text
    assert await seed_admin_from_env(db_session, "admin", "admin-pass-123") is False

    login = await auth_client.post(
        "/api/auth/login", json={"username": "admin", "password": "admin-pass-123"}
    )
    assert login.status_code == 401
    good = await auth_client.post(
        "/api/auth/login", json={"username": "admin", "password": "new-pass-456"}
    )
    assert good.status_code == 200


def test_cookie_flags():
    from app.core.security import set_auth_cookies
    from fastapi import Response

    response = Response()
    set_auth_cookies(response, "access-token", "refresh-token", secure=False)
    cookies = response.headers.getlist("set-cookie")
    assert len(cookies) == 2
    assert all("httponly" in c.lower() and "samesite=strict" in c.lower() for c in cookies)
    assert all("secure" not in c.lower() for c in cookies)
    # Cookie lifetime follows the configured JWT TTL, not a hardcoded value.
    response = Response()
    set_auth_cookies(response, "a", "r", secure=False, access_ttl_minutes=7, refresh_ttl_days=3)
    cookies = response.headers.getlist("set-cookie")
    lowered = [c.lower() for c in cookies]
    assert any("max-age=420" in c for c in lowered)
    assert any("max-age=259200" in c for c in lowered)


def test_env_ttl_names_are_honored():
    from app.core.config import Settings

    settings = Settings(
        _env_file=None,
        access_token_ttl_minutes=7,
        refresh_token_ttl_days=3,
        SECRET_KEY="x",
        DATABASE_URL_TEST="sqlite+aiosqlite:///:memory:",
    )
    assert settings.access_token_ttl_minutes == 7
    assert settings.refresh_token_ttl_days == 3


async def test_csrf_header_required(client, db_session):
    await seed_admin_from_env(db_session, "admin", "admin-pass-123")
    response = await client.post("/api/auth/logout")
    assert response.status_code == 403


async def test_rate_limit_after_five_failures(client, db_session):
    await seed_admin_from_env(db_session, "admin", "admin-pass-123")
    status_codes = [
        (await client.post("/api/auth/login", json={"username": "nobody", "password": "x"})).status_code
        for _ in range(6)
    ]
    assert status_codes[:5] == [401] * 5
    assert status_codes[5] == 429


async def test_revoked_jti_cannot_access(client, db_session):
    await seed_admin_from_env(db_session, "admin", "admin-pass-123")
    login = await client.post(
        "/api/auth/login", json={"username": "admin", "password": "admin-pass-123"}
    )
    assert login.status_code == 200
    rows = (await db_session.execute(select(TokenSession))).scalars().all()
    for row in rows:
        row.revoked_at = __import__("datetime").datetime.utcnow()
    await db_session.commit()
    me = await client.get("/api/auth/me")
    assert me.status_code == 401


def test_hash_is_not_plaintext():
    hashed = hash_password("correct horse battery staple")
    assert "correct horse" not in hashed
