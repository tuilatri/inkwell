# MODULE_MAP — inkwell

> Source of truth for repo structure. Line counts = non-empty source lines (`*.py`, `*.ts`, `*.tsx`, `*.css`), excluding `.venv/`, `__pycache__/`, `*.egg-info/`, `.chrome_profile/`, `node_modules/`, `dist/`, `test-results/`. Measured 2026-11-17.

## comix_downloader — Python (imported scraper) · 2.880 lines · 10 files

### `comix_downloader/` — 2.880 lines

| File | Lines | Role |
|---|---:|---|
| `comix_downloader/` | 2.880 | Imported Comix.to scraper (CLI, GUI, pagination, detectors, tests). Source: `D:\bato-downloader\src\comix_downloader`. Runtime data `.chrome_profile/` excluded. |

## novel_reader — FastAPI + React/Vite · 3.261 lines · 91 files

### `novel_reader/backend/` — 1.521 lines

| File | Lines | Role |
|---|---:|---|
| `novel_reader/backend/` | 1.521 | Auth (JWT cookies + argon2), filesystem scanner, name-only read APIs, Postgres FTS, Alembic migration, pytest suite. |

### `novel_reader/frontend/src/` — 1.740 lines

| File | Lines | Role |
|---|---:|---|
| `novel_reader/frontend/src/` | 1.740 | shadcn/ui (Radix + Tailwind v4) dark-theme SPA: login with password toggle, library TOC (names only, one horizontal scroll, bookmark), reader with top nav + fused progress, EN/VI tabs, search, Playwright E2E. |

## Pinned file sizes (doc-truth `lines:` claims — all git-listed files, non-empty lines)
| File | Non-empty lines |
|---|---:|
| `novel_reader/backend/app/main.py` | 68 |
| `novel_reader/frontend/src/pages/Reader.tsx` | 159 |
| `.opencode/skills/novel-reader-backend-conventions/SKILL.md` | 14 |
| `docs/ai-context/FRONTEND_MAP.md` | 30 |

## Conventions
- Line counts: non-empty source lines as defined in the header; dots are thousands separators ("5.670" = 5670).
- `doc-truth.mjs` `lines:<path>` claims measure **all** git-listed files under a path — do not reuse these source-only numbers in claims; use `exists:<path>` claims here.
- This table is parsed by doc-truth.mjs — keep the `| \`path\` | number |` row format.
