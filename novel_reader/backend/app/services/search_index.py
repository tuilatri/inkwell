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
    clauses = ["c.active = true"]
    if variant_id is not None:
        clauses.append("v.id = :vid")
        params["vid"] = variant_id

    if query:
        if dialect == "postgresql":
            # Prefix + accent-insensitive title/novel matching in addition to FTS
            # over content — "wire" now finds "Wireless_Onahole" without typing
            # the full name. websearch_to_tsquery alone only matched whole lexemes.
            clauses.append(
                "(s.tsv @@ websearch_to_tsquery('simple', unaccent(:q)) "
                "OR unaccent(c.title) ILIKE '%' || unaccent(:q) || '%' "
                "OR unaccent(n.title) ILIKE '%' || unaccent(:q) || '%')"
            )
            params["q"] = query
            order = (
                "CASE WHEN unaccent(c.title) ILIKE unaccent(:q) || '%' THEN 0 "
                "WHEN unaccent(n.title) ILIKE unaccent(:q) || '%' THEN 1 ELSE 2 END, "
                "c.number, c.title"
            )
        else:
            clauses.append(
                "(lower(s.tsv) LIKE :pattern OR lower(c.title) LIKE :pattern "
                "OR lower(n.title) LIKE :pattern)"
            )
            params["pattern"] = f"%{strip_accents(query).lower()}%"
            order = "c.number, c.title"
    else:
        # Empty query = "gợi ý" suggestions for the command palette.
        order = "c.id DESC"

    statement = text(
        "SELECT c.id, n.title, v.lang, c.title "
        "FROM chapters c "
        "LEFT JOIN chapter_search s ON s.chapter_id = c.id "
        "JOIN variants v ON v.id = c.variant_id "
        "JOIN novels n ON n.id = v.novel_id "
        "WHERE " + " AND ".join(clauses) + " "
        "ORDER BY " + order + " LIMIT :lim"
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
