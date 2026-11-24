from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.models import AdminUser, Chapter, Novel, ReadingState, Variant
from app.db.session import get_db
from app.schemas import ChapterOut, NovelOut, VariantOut

router = APIRouter(prefix="/api", tags=["library"])


@router.get("/novels", response_model=list[NovelOut])
async def list_novels(
    session: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
) -> list[NovelOut]:
    rows = (await session.execute(select(Novel).order_by(Novel.title))).scalars().all()
    return [
        NovelOut(
            id=row.id,
            title=row.title,
            kind="manga" if row.source_dir.startswith("manhwa:") else "novel",
        )
        for row in rows
    ]


@router.get("/novels/{novel_id}/variants", response_model=list[VariantOut])
async def list_variants(
    novel_id: int,
    session: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
) -> list[VariantOut]:
    rows = (
        await session.execute(
            select(Variant).where(Variant.novel_id == novel_id).order_by(Variant.lang)
        )
    ).scalars().all()
    return [VariantOut(id=row.id, lang=row.lang) for row in rows]


@router.get("/variants/{variant_id}/chapters", response_model=list[ChapterOut])
async def list_chapters(
    variant_id: int,
    session: AsyncSession = Depends(get_db),
    user: AdminUser = Depends(get_current_user),
) -> list[ChapterOut]:
    rows = (
        await session.execute(
            select(Chapter)
            .where(Chapter.variant_id == variant_id, Chapter.active.is_(True))
            .order_by(Chapter.number.is_(None), Chapter.number, Chapter.title)
        )
    ).scalars().all()
    visited = set(
        (
            await session.execute(
                select(ReadingState.chapter_id).where(
                    ReadingState.user_id == user.id,
                    (ReadingState.scroll_pos > 0) | (ReadingState.page_index.is_not(None)),
                )
            )
        ).scalars().all()
    )
    result: list[ChapterOut] = []
    for row in rows:
        result.append(ChapterOut(
            id=row.id,
            number=row.number,
            title=row.title,
            visited=row.id in visited,
            kind=row.kind,
            page_count=row.page_count,
        ))
    return result
