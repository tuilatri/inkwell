from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chapter, ChapterSearch, Novel, Variant
from app.services.paths import chapter_path
from app.services.text_reader import TextReadError, read_text


@dataclass(frozen=True)
class SearchHit:
    chapter_id: int
    novel_title: str
    lang: str
    chapter_title: str
    snippet: str


def strip_accents(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )


async def rebuild_search_index(session: AsyncSession) -> int:
    """Refresh the FTS index from disk. Postgres uses tsvector+unaccent;
    SQLite (unit tests only) stores accent-stripped lowercase text."""
    await session.execute(delete(ChapterSearch))
    dialect = session.bind.dialect.name
    chapters = (await session.execute(select(Chapter).where(Chapter.active.is_(True)))).scalars().all()
    indexed = 0
    for chapter in chapters:
        try:
            content = read_text(await chapter_path(chapter, session)).text
        except (TextReadError, OSError):
            continue
        if dialect == "postgresql":
            await session.execute(
                text(
                    "INSERT INTO chapter_search (chapter_id, tsv) "
                    "VALUES (:cid, to_tsvector('simple', unaccent(:content)))"
                ),
                {"cid": chapter.id, "content": content},
            )
        else:
            await session.execute(
                text("INSERT INTO chapter_search (chapter_id, tsv) VALUES (:cid, :content)"),
                {"cid": chapter.id, "content": strip_accents(content).lower()},
            )
        indexed += 1
    await session.commit()
    return indexed


async def search_chapters(
    session: AsyncSession,
    query: str,
    limit: int = 20,
    variant_id: int | None = None,
) -> list[SearchHit]:
    dialect = session.bind.dialect.name
    # The variant filter is composed, not passed as a nullable parameter:
    # asyncpg/PG18 cannot infer the type of ":vid" in "(:vid IS NULL OR ...)".
    params: dict[str, object] = {"lim": limit}
    if dialect == "postgresql":
        where = "s.tsv @@ websearch_to_tsquery('simple', unaccent(:q))"
        params["q"] = query
    else:
        where = "lower(s.tsv) LIKE :pattern"
        params["pattern"] = f"%{strip_accents(query).lower()}%"
    if variant_id is not None:
        where += " AND v.id = :vid"
        params["vid"] = variant_id
    statement = text(
        "SELECT c.id, n.title, v.lang, c.title "
        "FROM chapter_search s "
        "JOIN chapters c ON c.id = s.chapter_id "
        "JOIN variants v ON v.id = c.variant_id "
        "JOIN novels n ON n.id = v.novel_id "
        "WHERE " + where + " AND c.active = true "
        "LIMIT :lim"
    )
    rows = (await session.execute(statement, params)).all()

    hits: list[SearchHit] = []
    for chapter_id, novel_title, lang, chapter_title in rows:
        chapter = await session.get(Chapter, chapter_id)
        try:
            snippet = read_text(await chapter_path(chapter, session)).text[:160]
        except (TextReadError, OSError):
            snippet = ""
        hits.append(SearchHit(chapter_id, novel_title, lang, chapter_title, snippet))
    return hits
