from sqlalchemy import inspect


async def test_all_tables_created(db_session):
    connection = await db_session.connection()
    tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
    expected = {
        "novels", "variants", "chapters", "chapter_search", "admin_users",
        "token_sessions", "reading_state", "scan_log", "scan_warnings",
    }
    assert expected <= tables


async def test_variant_unique_constraint(db_session):
    from app.db.models import Novel, Variant
    from sqlalchemy.exc import IntegrityError

    novel = Novel(source_dir="X", slug="x", title="X")
    db_session.add(novel)
    await db_session.flush()
    db_session.add_all([Variant(novel_id=novel.id, lang="vi"), Variant(novel_id=novel.id, lang="vi")])
    try:
        await db_session.commit()
    except IntegrityError:
        await db_session.rollback()
    else:
        raise AssertionError("duplicate variant lang should fail")
