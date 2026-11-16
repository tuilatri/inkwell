# MODULE_MAP — inkwell

> Source of truth for repo structure. Line counts = non-empty (TESTING_GUIDE §1 convention).
> doc-truth.mjs parses the table below: `| \`path\` | number |` — keep the format when editing.

## comix_downloader — Python (imported scraper) · 2.670 lines · 10 files

### `comix_downloader/` — 2.670 lines

| File | Lines | Role |
|---|---:|---|
| `comix_downloader/` | 2.670 | Imported Comix.to scraper (CLI, GUI, pagination, detectors, tests). Source: `D:\bato-downloader\src\comix_downloader`. Runtime data `.chrome_profile/` excluded. |

## novel_reader — FastAPI + React/Vite · 1.697 lines · 45 files

### `novel_reader/backend/` — 1.348 lines

| File | Lines | Role |
|---|---:|---|
| `novel_reader/backend/` | 1.348 | Auth (JWT cookies + argon2), filesystem scanner, read APIs, Postgres FTS, Alembic migration, pytest suite. |

### `novel_reader/frontend/src/` — 349 lines

| File | Lines | Role |
|---|---:|---|
| `novel_reader/frontend/src/` | 349 | Dark-theme SPA: login, library, reader, EN/VI tabs, progress, search (TypeScript). |

## Conventions
- Line counts: non-empty lines (`git ls-files` + count non-empty lines)
- Numbers use dot thousands-separators: "5.670" = 5670
- This table is parsed by doc-truth.mjs — new rows must carry MEASURED numbers
