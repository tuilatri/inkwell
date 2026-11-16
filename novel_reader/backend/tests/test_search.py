from sqlalchemy import select

from app.core.config import get_settings
from app.db.models import Chapter
from app.services.search_index import rebuild_search_index, search_chapters, strip_accents
from app.services.scanner import scan_novels


def test_strip_accents():
    assert strip_accents("Chương") == "Chuong"


async def test_search_finds_vietnamese_without_accents(auth_client, db_session):
    await scan_novels(get_settings().novel_root, db_session)
    indexed = await rebuild_search_index(db_session)
    assert indexed >= 1

    hits = await search_chapters(db_session, "chuong 1")
    assert any(hit.chapter_title.startswith("Chapter_0001") for hit in hits)
    assert any("Chương 1" in hit.snippet for hit in hits)

    variants = (await auth_client.get("/api/novels/1/variants")).json()
    vi = next(item for item in variants if item["lang"] == "vi")
    scoped = await search_chapters(db_session, "chuong 1", variant_id=vi["id"])
    assert all(hit.lang == "vi" for hit in scoped)


async def test_empty_query_rejected(auth_client, db_session):
    response = await auth_client.get("/api/search", params={"q": "   "})
    assert response.status_code in (400, 422)


async def test_index_skips_unreadable_files(db_session, tmp_path):
    root = tmp_path / "Novel" / "chapters_vi"
    root.mkdir(parents=True)
    (root / "Chapter_0001_Bad.txt").write_bytes(b"\x81\x8d")
    await scan_novels(tmp_path, db_session)
    assert await rebuild_search_index(db_session) == 0
    assert (await db_session.execute(select(Chapter))).scalars().first() is not None
