# SPEC — Dockerize novel_reader

## Problem
The reader runs today only on the owner's Windows machine: backend needs a local `.venv`, frontend needs `npm`, and the verify gates hardcode Windows paths. Deploying or reproducing elsewhere is manual and brittle.

## Goal
One `docker compose up` starts the whole reader behind a single port, reusing the existing PostgreSQL databases, without copying novel text or secrets into images.

## Architecture
- `backend` image: Python 3.13 slim, `pip install -e ".[test]"`, uvicorn on `0.0.0.0:8000`; runs startup scan + auth as today.
- `frontend` image: Node 22 builds the Vite app, nginx serves the static build and proxies `/api` to `backend:8000`; published on `localhost:8080`.
- `docker-compose.yml`: `env_file: .env` (repo-local, untracked) supplies DB URLs and secrets; overrides `NOVEL_ROOT=/content/Novel` and `CORS_ORIGINS=http://localhost:8080`.
- `drafts/Novel/` bind-mounted read-only at `/content/Novel`. No database container by default — the two existing Postgres DBs are used via env.

## Cross-platform gates
`scripts/gate-cmd.mjs` dispatches to Windows (`node.exe`, `.venv/Scripts/python.exe`) or POSIX (`node`, `.venv/bin/python`) so `verify.mjs` works on both host and container/CI.

## Acceptance criteria
- [ ] `docker compose config` valid; images build; `docker compose up -d` healthy.
- [ ] `http://localhost:8080/` serves the SPA; unauthenticated `/api/novels` → 401; login → library (4 novels) → open chapter → progress/search work.
- [ ] No secret, `.env`, novel `.txt`, `node_modules` or `dist` baked into images (checked via `.dockerignore` + image file list).
- [ ] `drafts/Novel/` mounted `:ro`; backend cannot write content.
- [ ] Host `node scripts/verify.mjs` still 5/5 PASS after the gate wrapper change.

## Out of scope
Public TLS/Tailscale deployment, adding a Postgres container, changing the app's auth/DB design.
