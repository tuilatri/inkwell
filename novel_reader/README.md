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
3. Backend (always use the project-local virtual environment):
   ```
   cd backend
   python -m venv .venv
   .\.venv\Scripts\activate          # Windows
   # source .venv/bin/activate        # macOS/Linux
   pip install -e ".[test]"
   alembic upgrade head
   uvicorn app.main:app --reload --port 8000
   ```
   `.venv/`, `.pytest_cache/` and `*.egg-info/` are gitignored. Nothing is installed globally.
4. Frontend:
   ```
   cd frontend
   npm install
   npm run dev        # http://localhost:5173, /api proxied to :8000
   ```

## One-click start (Windows)

Double-click **`start.bat`** in this folder (Windows Explorer) — it always executes via `cmd.exe`, so VS Code never opens it as a text file. `start.py` remains the logic/CLI entry (`python start.py --no-browser`). The launcher:
- checks ports `8000`/`5173` and required files first (clear error message, no traceback);
- starts the backend in its own console using `backend/.venv/Scripts/python.exe -m uvicorn ... --reload`;
- starts the frontend in its own console using `npm run dev`;
- opens `http://localhost:5173` in your browser (use `python start.py --no-browser` to skip);
- **stops both servers** when you close the launcher window or press Ctrl+C there.

You can still run the two commands manually (below) — the launcher is only a convenience wrapper.

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
cd backend && .venv/Scripts/python.exe -m pytest -q
cd frontend && npx vitest run && npm run build
node ../../scripts/verify.mjs   # 5 gates (doc-truth, skills, pytest, vitest, build)
```

Postgres-specific tests require `DATABASE_URL_TEST` to be set to a real, empty PostgreSQL database. Without it they are skipped; SQLite-backed unit tests still run.

## Docker (single command)

```bash
cd novel_reader
# one-time: let the backend container reach Postgres on the host
copy .env .env.docker    # then replace localhost -> host.docker.internal in the two DB URLs
docker compose up -d --build    # SPA on http://localhost:8080
```

`docker-compose.yml` loads `.env` then `.env.docker` (gitignored overrides — see
`.env.docker.example`), mounts `drafts/Novel/` **read-only**, and forces
`ENVIRONMENT=local` (TEST DB) inside the container. On Windows/Docker Desktop the
bind-mounted first scan can take ~90 s; later starts use the mtime fingerprint.
Gates are cross-platform via root `package.json` scripts + `scripts/gate.mjs`.
