from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.schemas import SearchHitOut
from app.services.search_index import search_chapters

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search", response_model=list[SearchHitOut])
async def search(
    q: str = Query(min_length=1, max_length=200),
    variant_id: int | None = None,
    session: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
) -> list[SearchHitOut]:
    if not q.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="empty query")
    hits = await search_chapters(session, q.strip(), variant_id=variant_id)
    return [
        SearchHitOut(
            chapter_id=hit.chapter_id,
            novel_title=hit.novel_title,
            lang=hit.lang,
            chapter_title=hit.chapter_title,
            snippet=hit.snippet,
        )
        for hit in hits
    ]
