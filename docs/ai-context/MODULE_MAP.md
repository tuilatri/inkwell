# MODULE_MAP — inkwell

> Source of truth for repo structure. Line counts = non-empty source lines (`*.py`, `*.ts`, `*.tsx`, `*.css`), excluding `.venv/`, `__pycache__/`, `*.egg-info/`, `.chrome_profile/`, `node_modules/`, `dist/`, `test-results/`. Measured 2026-11-17.

## comix_downloader — Python (imported scraper) · 2.880 lines · 10 files

### `comix_downloader/` — 2.880 lines

| File | Lines | Role |
|---|---:|---|
| `comix_downloader/` | 2.880 | Imported Comix.to scraper (CLI, GUI, pagination, detectors, tests). Source: `D:\bato-downloader\src\comix_downloader`. Runtime data `.chrome_profile/` excluded. |

## novel_reader — FastAPI + React/Vite · 3.803 lines · 97 files

### `novel_reader/backend/` — 1.913 lines

| File | Lines | Role |
|---|---:|---|
| `novel_reader/backend/` | 1.913 | Auth (JWT cookies + argon2), dual-root fingerprint scanner (text + manga), pages/media APIs, Postgres FTS, Alembic migrations, pytest suite. |

### `novel_reader/frontend/src/` — 1.890 lines

| File | Lines | Role |
|---|---:|---|
| `novel_reader/frontend/src/` | 1.890 | shadcn/ui (Radix + Tailwind v4) dark-theme SPA: login with password toggle, library TOC (names only, one horizontal scroll, bookmark), text reader + MangaReader with page progress, EN/VI tabs, search, Playwright E2E. |
| `novel_reader/start.py` | 108 | Stdlib one-click launcher (double-click): port checks, venv uvicorn + npm dev in separate consoles, Ctrl+C / close-window stops both. |

## Pinned file sizes (doc-truth `lines:` claims — all git-listed files, non-empty lines)
| File | Non-empty lines |
|---|---:|
| `novel_reader/backend/app/main.py` | 68 |
| `novel_reader/frontend/src/pages/Reader.tsx` | 198 |
| `.opencode/skills/novel-reader-backend-conventions/SKILL.md` | 14 |
| `docs/ai-context/FRONTEND_MAP.md` | 32 |

## Conventions
- Line counts: non-empty source lines as defined in the header; dots are thousands separators ("5.670" = 5670).
- `doc-truth.mjs` `lines:<path>` claims measure **all** git-listed files under a path — do not reuse these source-only numbers in claims; use `exists:<path>` claims here.
- This table is parsed by doc-truth.mjs — keep the `| \`path\` | number |` row format.
