from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_csrf
from app.db.models import AdminUser, Chapter, ReadingState
from app.db.session import get_db
from app.schemas import ChapterOut, ProgressIn, ProgressOut
from app.services.paths import chapter_path
from app.services.text_reader import TextReadError, read_text

router = APIRouter(prefix="/api", tags=["reader"])


@router.get("/chapters/{chapter_id}", response_model=ChapterOut)
async def get_chapter(
    chapter_id: int,
    session: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
) -> ChapterOut:
    chapter = await session.get(Chapter, chapter_id)
    if chapter is None or not chapter.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="chapter not found")
    return ChapterOut(id=chapter.id, number=chapter.number, title=chapter.title)


@router.get("/chapters/{chapter_id}/content")
async def get_chapter_content(
    chapter_id: int,
    session: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
) -> PlainTextResponse:
    chapter = await session.get(Chapter, chapter_id)
    if chapter is None or not chapter.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="chapter not found")
    path = await chapter_path(chapter, session)
    try:
        content = read_text(path).text
    except (TextReadError, OSError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="chapter file unreadable")
    return PlainTextResponse(content, media_type="text/plain; charset=utf-8")


@router.put("/progress", response_model=ProgressOut, dependencies=[Depends(require_csrf)])
async def save_progress(
    payload: ProgressIn,
    user: AdminUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProgressOut:
    chapter = await session.get(Chapter, payload.chapter_id)
    if chapter is None or not chapter.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="chapter not found")
    state = await session.get(ReadingState, (user.id, payload.chapter_id))
    if state is None:
        state = ReadingState(user_id=user.id, chapter_id=payload.chapter_id, scroll_pos=payload.scroll_pos)
        session.add(state)
    else:
        state.scroll_pos = payload.scroll_pos
    await session.commit()
    return ProgressOut(chapter_id=payload.chapter_id, scroll_pos=payload.scroll_pos)


@router.get("/progress/{chapter_id}", response_model=ProgressOut)
async def get_progress(
    chapter_id: int,
    user: AdminUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProgressOut:
    state = await session.get(ReadingState, (user.id, chapter_id))
    return ProgressOut(chapter_id=chapter_id, scroll_pos=state.scroll_pos if state else 0.0)
