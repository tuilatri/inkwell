from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class MeOut(BaseModel):
    id: int
    username: str


class NovelOut(BaseModel):
    id: int
    title: str


class VariantOut(BaseModel):
    id: int
    lang: str


class ChapterOut(BaseModel):
    id: int
    number: int | None
    title: str
    visited: bool = False
    kind: str = "text"
    page_count: int = 0


class PageOut(BaseModel):
    index: int
    url: str


class ProgressIn(BaseModel):
    chapter_id: int
    scroll_pos: float = Field(default=0.0, ge=0.0)
    page_index: int | None = None


class ProgressOut(BaseModel):
    chapter_id: int
    scroll_pos: float
    page_index: int | None = None


class SearchHitOut(BaseModel):
    chapter_id: int
    novel_title: str
    lang: str
    chapter_title: str
    snippet: str


class ScanSummary(BaseModel):
    novels: int
    variants: int
    chapters: int
    warnings: int
