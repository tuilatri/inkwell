from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_csrf
from app.db.session import get_db
from app.schemas import ScanSummary
from app.services.scanner import scan_all
from app.services.search_index import rebuild_search_index

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/rescan", response_model=ScanSummary, dependencies=[Depends(require_csrf)])
async def rescan(
    session: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
) -> ScanSummary:
    result = await scan_all(get_root(), get_manga_root(), session, force=True)
    await rebuild_search_index(session)
    return ScanSummary(
        novels=result.novels,
        variants=result.variants,
        chapters=result.chapters,
        warnings=len(result.warnings),
    )


def get_root():
    from app.core.config import get_settings

    return get_settings().novel_root


def get_manga_root():
    from app.core.config import get_settings

    return get_settings().manhwa_root
