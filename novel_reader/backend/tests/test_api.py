from pathlib import Path

from sqlalchemy import select

from app.core.config import get_settings
from app.db.models import Chapter, Novel, ScanWarning
from app.services.scanner import scan_novels


def get_root():
    return get_settings().novel_root


async def test_security_headers(client):
    response = await client.get("/api/novels")
    assert response.status_code == 401
    assert "default-src 'self'" in response.headers["content-security-policy"]
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "no-store" in response.headers["cache-control"]


async def test_every_api_requires_auth(client, db_session):
    for path in ("/api/novels", "/api/auth/me", "/api/search?q=test"):
        response = await client.get(path)
        assert response.status_code == 401, path


async def test_library_lists_names_only(auth_client, db_session):
    await scan_novels(get_root(), db_session)
    response = await auth_client.get("/api/novels")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert set(body[0]) == {"id", "title"}
    assert body[0]["title"] == "Test Novel"


async def test_variant_switch_and_read(auth_client, db_session):
    await scan_novels(get_root(), db_session)
    novel = (await db_session.execute(select(Novel))).scalar_one()
    variants = (await auth_client.get(f"/api/novels/{novel.id}/variants")).json()
    assert {item["lang"] for item in variants} == {"vi", "en"}

    vi = next(item for item in variants if item["lang"] == "vi")
    chapters = (await auth_client.get(f"/api/variants/{vi['id']}/chapters")).json()
    assert [item["number"] for item in chapters] == [1, 2]

    content = await auth_client.get(f"/api/chapters/{chapters[0]['id']}/content")
    assert content.status_code == 200
    assert "Chương 1" in content.text


async def test_missing_content_file_is_404(auth_client, db_session):
    await scan_novels(get_root(), db_session)
    chapter = (await db_session.execute(select(Chapter))).scalars().first()
    path = get_root() / "Test Novel" / "chapters_vi" / chapter.rel_path
    original = path.read_bytes()
    path.unlink()
    try:
        response = await auth_client.get(f"/api/chapters/{chapter.id}/content")
        assert response.status_code == 404
    finally:
        path.write_bytes(original)


async def test_progress_round_trip(auth_client, db_session):
    await scan_novels(get_root(), db_session)
    chapter = (await db_session.execute(select(Chapter))).scalars().first()
    saved = await auth_client.put(
        "/api/progress",
        json={"chapter_id": chapter.id, "scroll_pos": 0.42},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert saved.status_code == 200
    loaded = await auth_client.get(f"/api/progress/{chapter.id}")
    assert loaded.json()["scroll_pos"] == 0.42


async def test_rescan(auth_client, db_session):
    response = await auth_client.post(
        "/api/admin/rescan", headers={"X-Requested-With": "XMLHttpRequest"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["novels"] >= 1
    assert isinstance((await db_session.execute(select(ScanWarning))).scalars().all(), list)
