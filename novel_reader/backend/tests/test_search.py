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


async def test_empty_query_returns_suggestions(auth_client, db_session):
    await scan_novels(get_settings().novel_root, db_session)
    await rebuild_search_index(db_session)
    response = await auth_client.get("/api/search", params={"q": "   "})
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert all(set(hit) == {"chapter_id", "novel_title", "lang", "chapter_title", "snippet"} for hit in response.json())


async def test_partial_prefix_search(db_session, tmp_path):
    lang_dir = tmp_path / "Wireless Onahole" / "chapters_vi"
    lang_dir.mkdir(parents=True)
    (lang_dir / "Chapter_0001_First.txt").write_text("nội dung", encoding="utf-8")
    await scan_novels(tmp_path, db_session)
    await rebuild_search_index(db_session)
    hits = await search_chapters(db_session, "wire")
    assert any(hit.novel_title == "Wireless Onahole" for hit in hits)


async def test_index_skips_unreadable_files(db_session, tmp_path):
    root = tmp_path / "Novel" / "chapters_vi"
    root.mkdir(parents=True)
    (root / "Chapter_0001_Bad.txt").write_bytes(b"\x81\x8d")
    await scan_novels(tmp_path, db_session)
    assert await rebuild_search_index(db_session) == 0
    assert (await db_session.execute(select(Chapter))).scalars().first() is not None
