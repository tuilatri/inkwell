# Inkwell Novel Reader

Private, single-admin reader for `.txt` novels stored in `drafts/Novel/`.

## Layout

```
novel_reader/
├── .env.example      placeholders only — copy to .env, never commit .env
├── backend/          FastAPI + SQLAlchemy + Alembic
├── frontend/         React + Vite + TypeScript (single dark theme)
└── drafts is NOT here: content lives in ../drafts/Novel/
```

## Setup

1. `cp .env.example .env` and fill in real values. `SECRET_KEY` must be a long random string.
2. DB links: the owner supplies two empty Postgres URLs (production + test). Development and migrations use **TEST** first. Production is never contacted without explicit approval.
3. Backend:
   ```
   cd backend
   pip install -e .
   alembic upgrade head
   uvicorn app.main:app --reload --port 8000
   ```
4. Frontend:
   ```
   cd frontend
   npm install
   npm run dev        # http://localhost:5173, /api proxied to :8000
   ```

## First login

On startup, if `admin_users` is empty, `ADMIN_USERNAME`/`ADMIN_PASSWORD` from `.env` are seeded (hashed with argon2id). After changing the password through the web UI, the seed never runs again — env credentials are void.

## Content rules

- Source: `NOVEL_ROOT/<novel>/chapters_vi/` and `chapters_en/` (one novel, two language tabs; VI default).
- Only `.txt` files become chapters. `_index.txt`, `*.json`, images and all other files are ignored.
- Both layouts are supported and may be mixed: flat `Chapter_001.txt`, or `Chapter 1 - Title/text.txt`.
- Text is streamed from disk. The DB holds metadata, a Postgres FTS index and reading state only.
- Broken files produce scan warnings, never a crash.

## Tests

```
cd backend && pytest -q
cd frontend && npx vitest run && npm run build
node ../../scripts/verify.mjs   # kit gate — "no gates yet" warning is expected
```

Postgres-specific tests require `DATABASE_URL_TEST` to be set to a real, empty PostgreSQL database. Without it they are skipped; SQLite-backed unit tests still run.
