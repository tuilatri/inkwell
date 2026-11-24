import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.security import seed_admin_from_env
from app.db.models import Chapter, Novel, ReadingState
from app.db.session import AsyncSessionLocal
from app.main import app
from app.services.scanner import fingerprint_images, scan_all, scan_manhwa


@pytest.fixture
async def manga_client(db_session):
    await seed_admin_from_env(db_session, "admin", "admin-pass-123")
    settings = get_settings()
    await scan_all(settings.novel_root, settings.manhwa_root, db_session)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login = await client.post("/api/auth/login", json={"username": "admin", "password": "admin-pass-123"})
        assert login.status_code == 200
        yield client


def test_fingerprint_images_stat_only():
    root = get_settings().manhwa_root
    assert len(fingerprint_images(root)) == 64


async def test_scan_manga_creates_image_chapters(db_session):
    root = get_settings().manhwa_root
    result = await scan_manhwa(root, db_session, force=True)
    assert result.chapters == 4  # 2 chapters x 2 languages
    rows = (
        await db_session.execute(select(Chapter).where(Chapter.kind == "images"))
    ).scalars().all()
    assert len(rows) == 4
    assert all(row.kind == "images" and row.page_count == 2 for row in rows)


async def test_manga_scan_is_idempotent(db_session):
    root = get_settings().manhwa_root
    first = await scan_manhwa(root, db_session)
    assert first.skipped is False
    second = await scan_manhwa(root, db_session)
    assert second.skipped is True


async def test_pages_and_media_auth_and_progress(manga_client, db_session):
    novels = (await manga_client.get("/api/novels")).json()
    manga = next(n for n in novels if n["title"] == "Manga Test (manga)")
    variants = (await manga_client.get(f"/api/novels/{manga['id']}/variants")).json()
    assert {v["lang"] for v in variants} == {"vi", "en"}
    en_variant = next(v for v in variants if v["lang"] == "en")
    chapters = (await manga_client.get(f"/api/variants/{en_variant['id']}/chapters")).json()
    assert chapters and all(chapter["kind"] == "images" for chapter in chapters), chapters

    target = chapters[0]
    pages = (await manga_client.get(f"/api/chapters/{target['id']}/pages")).json()
    assert [page["index"] for page in pages] == [1, 2]
    image = await manga_client.get(pages[0]["url"])
    assert image.status_code == 200

    saved = await manga_client.put(
        "/api/progress",
        json={"chapter_id": target["id"], "scroll_pos": 0, "page_index": 2},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert saved.status_code == 200
    progress = (await manga_client.get(f"/api/progress/{target['id']}")).json()
    assert progress["page_index"] == 2
    async with AsyncSessionLocal() as session:
        count = (await session.execute(select(func.count()).select_from(ReadingState))).scalar_one()
    assert count >= 1


async def test_media_rejects_unauth(client, db_session):
    response = await client.get("/api/media/1/1")
    assert response.status_code == 401
