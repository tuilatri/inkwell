# SPEC — Manga/Manhwa reading mode for novel_reader

## Problem
`drafts/Manhwa/` holds ~25.000 images across two reshaped titles (`chapters_en/Ch<N>/page_*.jpg`) but the reader only scans `.txt` under `NOVEL_ROOT`. Those chapters are invisible on the web.

## Goal
Serve image chapters alongside text chapters in the same app, with the owner's locked decisions (2026-11-24):
1. **Separate root** — `MANHWA_ROOT` in `.env` (default `../drafts/Manhwa`); text corpus untouched.
2. **Same VI/EN variants** as novels — titles already reshaped into `chapters_en/`; empty `chapters_vi` yields a friendly empty state, never an error.
3. **Progress by page index** for manga (text keeps pixel `scroll_pos`).

## Behavior
- Scanner: for each novel/variant under `MANHWA_ROOT`, each `Ch<N>/` folder with `page_*.{jpg,jpeg,png,webp}` becomes one chapter (`kind='images'`, `rel_path` = folder). stat-only fingerprint includes image paths + mtimes; new/renamed/deleted pages invalidate the skip.
- API: `GET /chapters/{id}/pages` → `[{index,url}]`; `GET /api/media/{chapter_id}/{page}` streams one image with auth + traversal guard + cache headers. `/content` remains text-only.
- UI: `MangaReader` renders images sequentially with lazy loading, `N/M` counter, zoom fit/actual, ←/→ page navigation; progress stored as `page_index`, restored on reopen. Library shows a "truyện tranh" badge and titles only (no covers).

## Acceptance criteria
- [ ] Both reshaped titles appear with VI/EN tabs; VI empty state is friendly.
- [ ] Opening a manga chapter loads pages lazily (no full 25k load), shows `N/M`.
- [ ] Advance page → reload → same page; text reading/progress/search/auth unchanged.
- [ ] Backend + frontend + E2E + inspector gates green; production DB untouched.

## Out of scope
comix_downloader changes, multi-group variants, PDF/CBZ export for manga, Docker, real `.env` edits.
