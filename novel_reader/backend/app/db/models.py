from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func, true
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# Postgres stores a real tsvector; SQLite (unit tests only) stores text.
TSVectorType = TSVECTOR().with_variant(Text(), "sqlite")


class Novel(Base):
    __tablename__ = "novels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # source_dir is the real filesystem key: two different folders may slugify
    # to the same string, but they must never share a row.
    source_dir: Mapped[str] = mapped_column(String(300), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(200), index=True)
    title: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Variant(Base):
    __tablename__ = "variants"
    __table_args__ = (UniqueConstraint("novel_id", "lang", name="uq_variants_novel_lang"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novels.id", ondelete="CASCADE"), index=True)
    lang: Mapped[str] = mapped_column(String(8))


class Chapter(Base):
    __tablename__ = "chapters"
    __table_args__ = (UniqueConstraint("variant_id", "rel_path", name="uq_chapters_variant_rel_path"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("variants.id", ondelete="CASCADE"), index=True)
    number: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    rel_path: Mapped[str] = mapped_column(String(1000))
    file_mtime: Mapped[float] = mapped_column(Float, default=0.0)
    byte_size: Mapped[int] = mapped_column(Integer, default=0)
    # Soft delete: a temporarily missing file must not erase reading history.
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true(), nullable=False)


class ChapterSearch(Base):
    __tablename__ = "chapter_search"

    chapter_id: Mapped[int] = mapped_column(
        ForeignKey("chapters.id", ondelete="CASCADE"), primary_key=True
    )
    tsv: Mapped[str] = mapped_column(TSVectorType, nullable=False)
    __table_args__ = (Index("ix_chapter_search_tsv", "tsv", postgresql_using="gin"),)


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class TokenSession(Base):
    __tablename__ = "token_sessions"

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("admin_users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(10))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ReadingState(Base):
    __tablename__ = "reading_state"

    user_id: Mapped[int] = mapped_column(ForeignKey("admin_users.id", ondelete="CASCADE"), primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapters.id", ondelete="CASCADE"), primary_key=True)
    scroll_pos: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class ScanLog(Base):
    __tablename__ = "scan_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    novels_upserted: Mapped[int] = mapped_column(Integer, default=0)
    chapters_upserted: Mapped[int] = mapped_column(Integer, default=0)
    fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)


class ScanWarning(Base):
    __tablename__ = "scan_warnings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_log_id: Mapped[int] = mapped_column(ForeignKey("scan_log.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(80))
    detail: Mapped[str] = mapped_column(String(1000))
