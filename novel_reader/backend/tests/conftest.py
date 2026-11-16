from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

# --- env must be set before importing any app module -------------------------
FIXTURE_ROOT = Path(tempfile.mkdtemp(prefix="inkwell-novel-test-")).resolve()
_novel = FIXTURE_ROOT / "Test Novel" / "chapters_vi"
_novel.mkdir(parents=True, exist_ok=True)
(_novel / "Chapter_0001_First.txt").write_text("Chương 1 nội dung đầu tiên", encoding="utf-8")
_chapter_dir = _novel / "Chapter 2 - Second"
_chapter_dir.mkdir(exist_ok=True)
(_chapter_dir / "text.txt").write_text("Chương 2 nội dung thứ hai", encoding="utf-8")
(_novel / "_index.txt").write_text("must be skipped", encoding="utf-8")
(_novel / "progress.json").write_text("{}", encoding="utf-8")
(_novel / "cover.jpg").write_bytes(b"\xff\xd8")
_en = FIXTURE_ROOT / "Test Novel" / "chapters_en"
_en.mkdir(exist_ok=True)
(_en / "Chapter_0001_English.txt").write_text("Chapter one English text", encoding="utf-8")

os.environ.setdefault("ENVIRONMENT", "local")
os.environ.setdefault("SECRET_KEY", "unit-test-secret-key-at-least-32-bytes-long")
# File-backed SQLite: the test session and the app's request sessions each
# need their own connection (:memory: + StaticPool deadlocks on concurrent checkout).
TEST_DB_PATH = FIXTURE_ROOT / "test.db"
os.environ.setdefault("DATABASE_URL_TEST", f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "admin-pass-123")
os.environ.setdefault("NOVEL_ROOT", str(FIXTURE_ROOT))

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.api.auth import _FAILED  # noqa: E402
from app.core.security import seed_admin_from_env  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import AsyncSessionLocal, async_engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_login_rate_limit():
    _FAILED.clear()


@pytest.fixture(scope="session", autouse=True)
async def dispose_engine_at_end():
    yield
    await async_engine.dispose()


@pytest.fixture
async def db_session():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session):
    await seed_admin_from_env(db_session, "admin", "admin-pass-123")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
async def auth_client(client):
    response = await client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin-pass-123"},
    )
    assert response.status_code == 200, response.text
    return client
