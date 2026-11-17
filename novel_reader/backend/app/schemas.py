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


class ProgressIn(BaseModel):
    chapter_id: int
    scroll_pos: float = Field(ge=0.0)


class ProgressOut(BaseModel):
    chapter_id: int
    scroll_pos: float


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
