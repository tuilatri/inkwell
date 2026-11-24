from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_csrf
from app.db.models import AdminUser, Chapter, ReadingState
from app.db.session import get_db
from app.schemas import ChapterOut, PageOut, ProgressIn, ProgressOut
from app.services.paths import chapter_path
from app.services.scanner import image_pages
from app.services.text_reader import TextReadError, read_text

router = APIRouter(prefix="/api", tags=["reader"])


async def _get_chapter(chapter_id: int, session: AsyncSession) -> Chapter:
    chapter = await session.get(Chapter, chapter_id)
    if chapter is None or not chapter.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="chapter not found")
    return chapter


@router.get("/chapters/{chapter_id}", response_model=ChapterOut)
async def get_chapter(
    chapter_id: int,
    session: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
) -> ChapterOut:
    chapter = await _get_chapter(chapter_id, session)
    return ChapterOut(
        id=chapter.id, number=chapter.number, title=chapter.title,
        kind=chapter.kind, page_count=chapter.page_count,
    )


@router.get("/chapters/{chapter_id}/content")
async def get_chapter_content(
    chapter_id: int,
    session: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
) -> PlainTextResponse:
    chapter = await _get_chapter(chapter_id, session)
    if chapter.kind != "text":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="image chapter — use /pages")
    path = await chapter_path(chapter, session)
    try:
        content = read_text(path).text
    except (TextReadError, OSError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="chapter file unreadable")
    return PlainTextResponse(content, media_type="text/plain; charset=utf-8")


@router.get("/chapters/{chapter_id}/pages", response_model=list[PageOut])
async def get_chapter_pages(
    chapter_id: int,
    session: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
) -> list[PageOut]:
    chapter = await _get_chapter(chapter_id, session)
    if chapter.kind != "images":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="not an image chapter")
    folder = await chapter_path(chapter, session)
    if not folder.is_dir():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="chapter folder missing")
    return [
        PageOut(index=index + 1, url=f"/api/media/{chapter_id}/{index + 1}")
        for index in range(len(image_pages(folder)))
    ]


@router.get("/media/{chapter_id}/{page}")
async def get_media(
    chapter_id: int,
    page: int,
    session: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
) -> FileResponse:
    chapter = await _get_chapter(chapter_id, session)
    if chapter.kind != "images":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not an image chapter")
    folder = await chapter_path(chapter, session)
    pages = image_pages(folder)
    if not 1 <= page <= len(pages):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="page not found")
    path: Path = pages[page - 1].resolve()
    if not path.is_relative_to(folder.resolve()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid page path")
    return FileResponse(path, headers={"Cache-Control": "private, max-age=3600"})


@router.put("/progress", response_model=ProgressOut, dependencies=[Depends(require_csrf)])
async def save_progress(
    payload: ProgressIn,
    user: AdminUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProgressOut:
    chapter = await _get_chapter(payload.chapter_id, session)
    state = await session.get(ReadingState, (user.id, payload.chapter_id))
    if state is None:
        state = ReadingState(user_id=user.id, chapter_id=payload.chapter_id)
        session.add(state)
    state.scroll_pos = payload.scroll_pos
    state.page_index = payload.page_index
    await session.commit()
    return ProgressOut(chapter_id=payload.chapter_id, scroll_pos=state.scroll_pos, page_index=state.page_index)


@router.get("/progress/{chapter_id}", response_model=ProgressOut)
async def get_progress(
    chapter_id: int,
    user: AdminUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProgressOut:
    state = await session.get(ReadingState, (user.id, chapter_id))
    return ProgressOut(
        chapter_id=chapter_id,
        scroll_pos=state.scroll_pos if state else 0.0,
        page_index=state.page_index if state else None,
    )
