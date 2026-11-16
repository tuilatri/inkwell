# ARCHITECTURE — inkwell

> Overall architecture. Code wins over this doc when they disagree.

## 1. Stack & Apps
- `comix_downloader/` — Python scraper (CLI + GUI) for Comix.to; source imported from `D:\bato-downloader\src\comix_downloader`. Downloads chapter images/text to disk; uses real Chrome via undetected-chromedriver. Runtime data `.chrome_profile/` is gitignored.
- `novel_reader/backend/` — Python 3.13 + FastAPI + SQLAlchemy async + Alembic + asyncpg; serves the reader API on :8000 from a project-local `.venv`.
- `novel_reader/frontend/` — React 18 + Vite 6 + TypeScript + Tailwind v4 + shadcn/ui (Radix); SPA on :5173, `/api` proxied to backend.

## 2. Services & Modules
- `app/core/config.py` — pydantic-settings from `novel_reader/.env`; converts plain `postgresql://` links to `postgresql+asyncpg://`; active DB = TEST unless `ENVIRONMENT=production`.
- `app/core/security.py` — argon2id hashing, JWT create/decode, cookie set/clear, admin seeding from env.
- `app/core/deps.py` — `get_current_user` (access cookie + jti check), `require_csrf` (unsafe-method header check).
- `app/services/scanner.py` — walks `drafts/Novel/<novel>/chapters_{vi,en}/`, handles flat and chapter-folder layouts, soft-deletes stale chapters, writes warnings.
- `app/services/text_reader.py` — UTF-8 → cp1252 fallback; never crashes a scan on a bad file.
- `app/services/search_index.py` — rebuilds `chapter_search` tsvector via Postgres `to_tsvector('simple', unaccent(text))`; prefix search also matches titles with `unaccent(...) ILIKE`.
- `app/services/paths.py` — resolves chapter files, refuses paths outside the content root.

## 3. Data Layer (schema, DB convention)
- PostgreSQL 18, two databases (TEST/PRODUCTION), Alembic revisions `0001_initial` → `0002_source_dir_and_soft_delete`.
- Tables: `novels(source_dir unique, slug, title)`, `variants(unique novel_id+lang)`, `chapters(unique variant_id+rel_path, number, active)`, `chapter_search(chapter_id PK/FK, tsv tsvector + GIN)`, `admin_users`, `token_sessions(jti PK, kind, expires_at, revoked_at)`, `reading_state(user_id+chapter_id PK, scroll_pos)`, `scan_log`, `scan_warnings`.
- Text stays on disk; DB stores metadata, search index and reading state only.

## 4. API Surface
See `API_MAP.md` — 14 endpoints, all auth-protected, CSRF on mutations.

## 5. Security (auth, secrets, rate limits)
- One admin, seeded from `.env` only when `admin_users` is empty; password change through UI voids env credentials.
- JWT in HttpOnly cookies, `jti` revocation, `SameSite=Strict`, `Secure` in production; CSRF header on mutations; login rate-limit 5/60 s.
- Secrets live in untracked `novel_reader/.env`; never committed or logged. At-rest story = disk encryption (BitLocker/LUKS) + encrypted backups; no per-column app encryption (source text is plaintext on disk).
- CSP, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, no-store on API.

## 6. Integrations
- Comix.to scraping (separate app, disk output into `drafts/Novel/`), Google Fonts (Newsreader + IBM Plex Sans), GitNexus MCP tools (tool-managed, never vendored), OpenCode/Claude skills from `.claude/skills` + `.opencode/skills`.

## 7. Known Limits & Constraints
- Startup scans the full corpus (~5.300 txt / 90 MB) — 40–60 s; incremental scan is deferred.
- Anti-scrape/anti-extension is best-effort (auth + headers); for public deployment use Tailscale/IP allowlist.
- Single-admin design; no Docker yet; no light theme; reading position is per chapter (pixel offset).
