from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chapter, Novel, ScanLog, ScanWarning, Variant

NUMBER_RE = re.compile(r"\d+")
LANGS = ("vi", "en")
SKIP_PREFIXES = ("_", ".")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
MANGA_FP_PREFIX = "manga:"


@dataclass
class ScanResult:
    novels: int = 0
    variants: int = 0
    chapters: int = 0
    warnings: list[ScanWarning] = field(default_factory=list)
    skipped: bool = False


def fingerprint(root: Path) -> str:
    """Cheap content-root signature: relative .txt paths + mtime, no file reads."""
    if not root.is_dir():
        return ""
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.txt")):
        if not path.is_file() or path.name.startswith(SKIP_PREFIXES):
            continue
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(str(path.stat().st_mtime_ns).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def slugify(title: str) -> str:
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_title).strip("-").lower()
    return slug or "untitled"


def parse_chapter(path: Path, lang_root: Path) -> tuple[int | None, str, str]:
    """Return (number, title, rel_path) using filename first, then parent folder."""
    rel_path = path.relative_to(lang_root).as_posix()
    stem_match = NUMBER_RE.search(path.stem)
    if stem_match:
        number = int(stem_match.group())
        title = path.stem
    else:
        parent_match = NUMBER_RE.search(path.parent.name) if path.parent != lang_root else None
        number = int(parent_match.group()) if parent_match else None
        title = path.parent.name if parent_match else path.stem
    return number, title[:500], rel_path


async def _warn(session: AsyncSession, result: ScanResult, scan_log_id: int, kind: str, detail: str) -> None:
    warning = ScanWarning(scan_log_id=scan_log_id, kind=kind, detail=detail[:1000])
    session.add(warning)
    result.warnings.append(warning)


async def scan_novels(root: Path, session: AsyncSession, force: bool = False) -> ScanResult:
    result = ScanResult()
    current = fingerprint(root)
    if not force:
        last = (
            await session.execute(
                select(ScanLog)
                .where(
                    ScanLog.finished_at.is_not(None),
                    ~ScanLog.fingerprint.like(f"{MANGA_FP_PREFIX}%"),
                )
                .order_by(ScanLog.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if last is not None and last.fingerprint == current:
            result.skipped = True
            result.novels = int((await session.execute(select(func.count()).select_from(Novel))).scalar_one())
            result.chapters = int(
                (await session.execute(select(func.count()).select_from(Chapter).where(Chapter.active.is_(True)))).scalar_one()
            )
            return result

    scan_log = ScanLog(started_at=_utcnow(), fingerprint=current)
    session.add(scan_log)
    await session.flush()

    if not root.is_dir():
        await _warn(session, result, scan_log.id, "root_missing", str(root))
        scan_log.finished_at = _utcnow()
        await session.commit()
        return result

    for novel_dir in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith(SKIP_PREFIXES)):
        novel = (
            await session.execute(select(Novel).where(Novel.source_dir == novel_dir.name))
        ).scalar_one_or_none()
        if novel is None:
            novel = Novel(
                source_dir=novel_dir.name, slug=slugify(novel_dir.name), title=novel_dir.name
            )
            session.add(novel)
            await session.flush()
        result.novels += 1

        for lang in LANGS:
            lang_root = novel_dir / f"chapters_{lang}"
            if not lang_root.is_dir():
                continue
            variant = (
                await session.execute(
                    select(Variant).where(Variant.novel_id == novel.id, Variant.lang == lang)
                )
            ).scalar_one_or_none()
            if variant is None:
                variant = Variant(novel_id=novel.id, lang=lang)
                session.add(variant)
                await session.flush()
            result.variants += 1

            existing = {
                row.rel_path: row
                for row in (await session.execute(select(Chapter).where(Chapter.variant_id == variant.id))).scalars()
            }
            seen_paths: set[str] = set()
            seen_numbers: dict[int, str] = {}
            for path in sorted(
                p for p in lang_root.rglob("*.txt")
                if not p.name.startswith(SKIP_PREFIXES) and p.is_file()
            ):
                number, title, rel_path = parse_chapter(path, lang_root)
                seen_paths.add(rel_path)
                if number is not None and number in seen_numbers:
                    await _warn(
                        session, result, scan_log.id, "duplicate_number",
                        f"{novel_dir.name}/{lang}: {rel_path} duplicates {seen_numbers[number]}",
                    )
                    continue
                if number is not None:
                    seen_numbers[number] = rel_path
                stat = path.stat()
                chapter = existing.get(rel_path)
                if chapter is None:
                    chapter = Chapter(variant_id=variant.id)
                    session.add(chapter)
                chapter.number = number
                chapter.title = title
                chapter.rel_path = rel_path
                chapter.file_mtime = stat.st_mtime
                chapter.byte_size = stat.st_size
                chapter.active = True  # reappearing file reuses the same row (and its reading state)
                result.chapters += 1

            for rel_path, chapter in existing.items():
                if rel_path not in seen_paths and chapter.active:
                    # Soft-delete: reading_state and search rows stay attached to
                    # this chapter id if the file comes back later.
                    chapter.active = False
                    await _warn(session, result, scan_log.id, "missing_file", f"{novel_dir.name}/{lang}: {rel_path}")

    scan_log.novels_upserted = result.novels
    scan_log.chapters_upserted = result.chapters
    scan_log.finished_at = _utcnow()
    await session.commit()
    return result


def image_pages(folder: Path) -> list[Path]:
    """Sorted page images of one manga chapter folder (stat-only metadata)."""
    return sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES and p.name.startswith("page_")
    )


def fingerprint_images(root: Path) -> str:
    if not root.is_dir():
        return ""
    digest = hashlib.sha256()
    for folder in sorted(p for p in root.rglob("*") if p.is_dir()):
        for page in image_pages(folder):
            stat = page.stat()
            digest.update(page.relative_to(root).as_posix().encode("utf-8"))
            digest.update(str(stat.st_mtime_ns).encode("ascii"))
            digest.update(str(stat.st_size).encode("ascii"))
            digest.update(b"\0")
    return digest.hexdigest()


async def scan_manhwa(root: Path, session: AsyncSession, force: bool = False) -> ScanResult:
    """Image analogue of scan_novels — chapters are folders of page_*.{jpg,...}."""
    result = ScanResult()
    current = MANGA_FP_PREFIX + fingerprint_images(root)
    if not force:
        last = (
            await session.execute(
                select(ScanLog)
                .where(
                    ScanLog.finished_at.is_not(None),
                    ScanLog.fingerprint.like(f"{MANGA_FP_PREFIX}%"),
                )
                .order_by(ScanLog.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if last is not None and last.fingerprint == current:
            result.skipped = True
            result.novels = int((await session.execute(select(func.count()).select_from(Novel))).scalar_one())
            result.chapters = int(
                (await session.execute(select(func.count()).select_from(Chapter).where(Chapter.active.is_(True)))).scalar_one()
            )
            return result

    scan_log = ScanLog(started_at=_utcnow(), fingerprint=current)
    session.add(scan_log)
    await session.flush()
    if not root.is_dir():
        scan_log.finished_at = _utcnow()
        await session.commit()
        return result

    for novel_dir in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith(SKIP_PREFIXES)):
        # Prefix source_dir: a title may exist in both roots (e.g. Wireless_Onahole).
        source = f"manhwa:{novel_dir.name}"
        novel = (
            await session.execute(select(Novel).where(Novel.source_dir == source))
        ).scalar_one_or_none()
        if novel is None:
            novel = Novel(source_dir=source, slug=slugify(novel_dir.name), title=f"{novel_dir.name} (manga)")
            session.add(novel)
            await session.flush()
        result.novels += 1

        for lang in LANGS:
            lang_root = novel_dir / f"chapters_{lang}"
            if not lang_root.is_dir():
                continue  # missing VI is not an error — the UI shows an empty tab
            variant = (
                await session.execute(
                    select(Variant).where(Variant.novel_id == novel.id, Variant.lang == lang)
                )
            ).scalar_one_or_none()
            if variant is None:
                variant = Variant(novel_id=novel.id, lang=lang)
                session.add(variant)
                await session.flush()
            result.variants += 1

            existing = {
                row.rel_path: row
                for row in (await session.execute(select(Chapter).where(Chapter.variant_id == variant.id))).scalars()
            }
            seen_paths: set[str] = set()
            seen_numbers: dict[int, str] = {}
            for folder in sorted(p for p in lang_root.iterdir() if p.is_dir() and not p.name.startswith(SKIP_PREFIXES)):
                pages = image_pages(folder)
                if not pages:
                    continue
                rel_path = folder.relative_to(lang_root).as_posix()
                number = int(NUMBER_RE.search(folder.name).group()) if NUMBER_RE.search(folder.name) else None
                seen_paths.add(rel_path)
                if number is not None and number in seen_numbers:
                    await _warn(session, result, scan_log.id, "duplicate_number",
                                f"{novel_dir.name}/{lang}: {rel_path} duplicates {seen_numbers[number]}")
                    continue
                if number is not None:
                    seen_numbers[number] = rel_path
                stats = [page.stat() for page in pages]
                chapter = existing.get(rel_path)
                if chapter is None:
                    chapter = Chapter(variant_id=variant.id, kind="images")
                    session.add(chapter)
                chapter.number = number
                chapter.title = folder.name[:500]
                chapter.rel_path = rel_path
                chapter.file_mtime = max(stat.st_mtime for stat in stats)
                chapter.byte_size = sum(stat.st_size for stat in stats)
                chapter.page_count = len(pages)
                chapter.active = True
                result.chapters += 1

            for rel_path, chapter in existing.items():
                if rel_path not in seen_paths and chapter.active:
                    chapter.active = False
                    await _warn(session, result, scan_log.id, "missing_file", f"{novel_dir.name}/{lang}: {rel_path}")

    scan_log.novels_upserted = result.novels
    scan_log.chapters_upserted = result.chapters
    scan_log.finished_at = _utcnow()
    await session.commit()
    return result


async def scan_all(novel_root: Path, manhwa_root: Path, session: AsyncSession, force: bool = False) -> ScanResult:
    """Scan both corpora; counts are additive, skip decisions independent."""
    text = await scan_novels(novel_root, session, force=force)
    manga = await scan_manhwa(manhwa_root, session, force=force)
    text.novels += manga.novels
    text.variants += manga.variants
    text.chapters += manga.chapters
    text.warnings.extend(manga.warnings)
    text.skipped = text.skipped and manga.skipped
    return text


def _utcnow():
    from datetime import datetime

    return datetime.utcnow()
