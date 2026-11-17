import os

from sqlalchemy import select

from app.db.models import Chapter, ScanLog
from app.services.scanner import ScanResult, parse_chapter, scan_novels, slugify


def test_parse_chapter_both_layouts(tmp_path):
    lang_root = tmp_path / "chapters_vi"
    flat = lang_root / "Chapter_0007_Flat.txt"
    nested_dir = lang_root / "Chapter 8 - Nested"
    nested_dir.mkdir(parents=True)
    nested = nested_dir / "text.txt"
    assert parse_chapter(flat, lang_root)[:2] == (7, "Chapter_0007_Flat")
    assert parse_chapter(nested, lang_root)[:2] == (8, "Chapter 8 - Nested")


def test_slugify_vietnamese():
    assert slugify("Solo Farming In The Tower") == "solo-farming-in-the-tower"


async def test_unchanged_tree_skips_second_scan(db_session, tmp_path):
    lang = tmp_path / "Novel" / "chapters_vi"
    lang.mkdir(parents=True)
    (lang / "Chapter_0001_A.txt").write_text("nội dung", encoding="utf-8")

    first = await scan_novels(tmp_path, db_session)
    assert first.skipped is False
    second = await scan_novels(tmp_path, db_session)
    assert second.skipped is True
    assert second.chapters == first.chapters
    logs = (await db_session.execute(select(ScanLog))).scalars().all()
    assert len(logs) == 1  # a skip writes no new scan_log


async def test_touch_or_add_invalidates_fingerprint(db_session, tmp_path):
    lang = tmp_path / "Novel" / "chapters_vi"
    lang.mkdir(parents=True)
    chapter = lang / "Chapter_0001_A.txt"
    chapter.write_text("nội dung", encoding="utf-8")
    await scan_novels(tmp_path, db_session)

    stat = chapter.stat()
    os.utime(chapter, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
    touched = await scan_novels(tmp_path, db_session)
    assert touched.skipped is False

    (lang / "Chapter_0002_B.txt").write_text("thêm", encoding="utf-8")
    added = await scan_novels(tmp_path, db_session)
    assert added.skipped is False
    assert added.chapters == 2


async def test_force_rescans_even_when_unchanged(db_session, tmp_path):
    lang = tmp_path / "Novel" / "chapters_vi"
    lang.mkdir(parents=True)
    (lang / "Chapter_0001_A.txt").write_text("nội dung", encoding="utf-8")
    await scan_novels(tmp_path, db_session)
    forced = await scan_novels(tmp_path, db_session, force=True)
    assert forced.skipped is False


async def test_scan_mixed_layout_and_skip_rules(db_session, tmp_path):
    root = tmp_path / "Novel"
    vi = root / "Bộ truyện A" / "chapters_vi"
    vi.mkdir(parents=True)
    (vi / "Chapter_0001_Flat.txt").write_text("flat", encoding="utf-8")
    nested = vi / "Chapter 2 - Nested"
    nested.mkdir()
    (nested / "text.txt").write_text("nested", encoding="utf-8")
    (vi / "_index.txt").write_text("skip me", encoding="utf-8")
    (vi / "progress.json").write_text("{}", encoding="utf-8")
    (vi / "cover.jpg").write_bytes(b"\xff\xd8")
    en = root / "Bộ truyện A" / "chapters_en"
    en.mkdir()
    (en / "Chapter_0001_English.txt").write_text("en", encoding="utf-8")

    result = await scan_novels(root, db_session)
    assert isinstance(result, ScanResult)
    assert result.novels == 1
    assert result.variants == 2
    assert result.chapters == 3
    assert all(w.kind != "duplicate_number" for w in result.warnings)
    assert len([w for w in result.warnings if w.kind == "missing_file"]) == 0

    from sqlalchemy import select

    from app.db.models import Chapter

    titles = {row.title for row in (await db_session.execute(select(Chapter))).scalars()}
    assert "_index" not in titles
    assert "progress" not in titles

    # Removing a file is detected on the next scan, not silently ignored.
    (vi / "Chapter_0001_Flat.txt").unlink()
    second = await scan_novels(root, db_session)
    assert second.chapters == 2
    assert any(w.kind == "missing_file" for w in second.warnings)


async def test_duplicate_number_warns(db_session, tmp_path):
    vi = tmp_path / "Truyện B" / "chapters_vi"
    vi.mkdir(parents=True)
    (vi / "Chapter_0001_A.txt").write_text("a", encoding="utf-8")
    (vi / "Chapter_0001_B.txt").write_text("b", encoding="utf-8")
    result = await scan_novels(tmp_path, db_session)
    assert result.chapters == 1
    assert any(w.kind == "duplicate_number" for w in result.warnings)


async def test_soft_delete_preserves_reading_state(db_session, tmp_path):
    from app.db.models import AdminUser, ReadingState

    vi = tmp_path / "Novel" / "chapters_vi"
    vi.mkdir(parents=True)
    file = vi / "Chapter_0001_A.txt"
    file.write_text("a", encoding="utf-8")
    await scan_novels(tmp_path, db_session)
    chapter = (await db_session.execute(select(Chapter))).scalars().first()
    admin = AdminUser(username="admin", password_hash="x")
    db_session.add(admin)
    await db_session.flush()
    db_session.add(ReadingState(user_id=admin.id, chapter_id=chapter.id, scroll_pos=0.75))
    await db_session.commit()

    file.unlink()
    await scan_novels(tmp_path, db_session)
    await db_session.refresh(chapter)
    assert chapter.active is False
    assert (await db_session.get(ReadingState, (admin.id, chapter.id))).scroll_pos == 0.75

    file.write_text("a", encoding="utf-8")
    await scan_novels(tmp_path, db_session)
    await db_session.refresh(chapter)
    assert chapter.active is True
    assert (await db_session.get(ReadingState, (admin.id, chapter.id))).scroll_pos == 0.75


async def test_same_slug_different_folders_are_distinct(db_session, tmp_path):
    for name in ("Light Novel", "light-novel"):
        lang_dir = tmp_path / name / "chapters_vi"
        lang_dir.mkdir(parents=True)
        (lang_dir / "Chapter_0001_A.txt").write_text("x", encoding="utf-8")
    result = await scan_novels(tmp_path, db_session)
    assert result.novels == 2
