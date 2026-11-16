from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import admin as admin_api
from app.api import auth as auth_api
from app.api import chapters as chapters_api
from app.api import novels as novels_api
from app.api import search as search_api
from app.core.config import get_settings
from app.core.security import seed_admin_from_env
from app.db.session import AsyncSessionLocal
from app.services.scanner import scan_novels
from app.services.search_index import rebuild_search_index

log = logging.getLogger("novel_reader")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.validate_required()
    async with AsyncSessionLocal() as session:
        try:
            await seed_admin_from_env(
                session, settings.admin_username, settings.admin_password
            )
            result = await scan_novels(settings.novel_root, session)
            indexed = await rebuild_search_index(session)
            log.info(
                "startup scan: novels=%s chapters=%s warnings=%s indexed=%s",
                result.novels, result.chapters, len(result.warnings), indexed,
            )
        except Exception:
            log.exception("startup scan failed; the app will still start")
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; frame-ancestors 'none'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, private"
        return response

    for router in (
        auth_api.router,
        novels_api.router,
        chapters_api.router,
        search_api.router,
        admin_api.router,
    ):
        app.include_router(router)
    return app


app = create_app()
