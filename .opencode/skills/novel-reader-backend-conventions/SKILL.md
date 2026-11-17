---
name: novel-reader-backend-conventions
description: Hard rules for novel_reader/backend/** — use when changing FastAPI routes, auth/JWT cookies, filesystem scanning, Postgres FTS, Alembic migrations, pytest tests or the project-local venv. Also use when editing API_MAP.md or TESTING_GUIDE.md.
metadata:
  scope: novel_reader/backend/**, docs/ai-context/API_MAP.md, docs/ai-context/TESTING_GUIDE.md
---

# Novel reader backend conventions

Rule 0 — **Use the venv, never global Python.** `cd novel_reader/backend && .\.venv\Scripts\python.exe -m pytest -q`; install with `pip install -e ".[test]"`. Why: the app is isolated and reproducible. Example: `python -m venv .venv` on a fresh clone.

Rule 1 — **Content lives on disk.** `drafts/Novel/` is gitignored source data; scanner reads `.txt` at any depth (flat `Ch_001.txt` or `Chapter 1/text.txt`), skips `_index.txt`/`*.json`/images, soft-deletes stale chapters (`active=false`) so reading state survives. Never move text into the DB. Example: `app/services/scanner.py`.

Rule 2 — **Auth is cookie-only and revocable.** argon2id hash, JWT in `nr_access`/`nr_refresh` HttpOnly cookies, `jti` in `token_sessions`, `X-Requested-With` CSRF on mutations, login rate-limit 5/60 s. No token in localStorage or logs. Example: `app/core/security.py`, `app/core/deps.py`.

Rule 3 — **Postgres specifics are deliberate.** Async driver `postgresql+asyncpg://` (config normalizes plain provider links); active DB = TEST unless `ENVIRONMENT=production`; Alembic `0001_initial` → `0002_source_dir_and_soft_delete`; production is touched only on explicit owner request. Example: never hardcode a DB URL in source.

Rule 4 — **Search is accent-insensitive prefix, not just FTS.** Combine `tsvector('simple', unaccent(text))` with `unaccent(title) ILIKE '%' || unaccent(:q) || '%'`; compose the variant filter instead of `:vid IS NULL` (asyncpg/PG18 ambiguity). Empty `q` returns suggestions. Example: `app/services/search_index.py`.

Rule 5 — **Every API route is auth-protected.** New endpoints depend on `get_current_user`, mutations also on `require_csrf`; responses get no-store + security headers from `app/main.py`. Update `API_MAP.md` in the same change.

Rule 6 — **Measure, don't guess.** Update `TESTING_GUIDE.md` §1 only after running the suites; backend tests use a SQLite file DB in `tests/conftest.py`, Postgres FTS is checked live. Expected baseline: 31 pytest items.
