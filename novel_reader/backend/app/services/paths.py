from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import Chapter, Novel, Variant


async def chapter_path(chapter: Chapter, session: AsyncSession) -> Path:
    """Resolve a chapter's text file, refusing any path outside the content root."""
    variant = await session.get(Variant, chapter.variant_id)
    novel = await session.get(Novel, variant.novel_id)
    root = get_settings().novel_root.resolve()
    path = (root / novel.title / f"chapters_{variant.lang}" / chapter.rel_path).resolve()
    if not path.is_relative_to(root):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid chapter path")
    return path
