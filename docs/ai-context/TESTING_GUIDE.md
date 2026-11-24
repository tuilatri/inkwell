# TESTING_GUIDE — inkwell

## 1. Current test counts (doc-truth parses this table — NEVER guess)

| **40** | **collected pytest items** (backend, project venv) |
|---|---|
| **27** | **Vitest tests** (frontend components) |
| **2** | **Playwright E2E tests** (full browser flow) |

Measured 2026-11-17; numbers use dot as thousands separator when ≥1000.

## 2. How to run

For everyday use, double-click `novel_reader/start.bat` in Windows Explorer (a thin `cmd.exe` wrapper that always executes, never opens in VS Code); it calls `start.py`, which starts both dev servers in separate windows and stops them together. `python novel_reader/start.py --no-browser` stays the CLI equivalent. The commands below remain the source of truth for verification.

```bash
# Backend (from novel_reader/backend, venv only)
.\.venv\Scripts\python.exe -m pytest -q

# Frontend (from novel_reader/frontend)
npx vitest run
npm run build
npx playwright test          # needs Chrome channel + .env credentials + backend :8000

# Harness gates (from repo root)
node scripts/verify.mjs      # serial fail-fast, gates in kit.config.json
node scripts/verify.mjs --fast   # only docs-truth + skills-integrity (gates tagged "slow" skipped)
node scripts/doc-truth.mjs   # claims in kit.config.json alone
```

`.githooks/pre-commit` runs the `--fast` guard before each commit; enable it in a
fresh clone with `git config core.hooksPath .githooks` (already set in this clone).
Gate commands are cross-platform via root `package.json` scripts + `scripts/gate.mjs` (Windows venv vs POSIX venv).
Docker smoke: `cd novel_reader && docker compose up -d --build`, then `curl localhost:8080/` → 200 SPA, `/api/novels` unauth → 401, login → library → search.
Gates tagged `slow` = backend-tests, frontend-tests, frontend-build — full suite
runs in `.github/workflows/ci.yml` on push to `main`/`feat/**` and PRs to `main`
(windows-latest, Python 3.13 + Node 22, backend venv + `pip install -e ".[test]"`,
frontend `npm ci`, then `node scripts/verify.mjs`). CI needs no secrets: tests use
SQLite/env overrides and E2E is not part of the gate suite.

Playwright reads `ADMIN_USERNAME`/`ADMIN_PASSWORD` from the untracked `novel_reader/.env` and skips login-dependent checks if absent. Dev servers are started by `playwright.config.ts` (Vite :5173 + uvicorn :8000).

## 3. Test-writing conventions
- TDD where practical: write the failing test, run it, implement, run again, then commit.
- Backend tests use SQLite file DB in `tests/conftest.py`; no Postgres needed for unit tests. Postgres-specific FTS is verified by live checks.
- Frontend jsdom needs `src/test-setup.ts` shims (ResizeObserver, scrollIntoView, offset dimensions) for Radix/virtualizer.
- E2E must assert **layout facts** (e.g. popup `boundingBox().y > 0`), not only `toBeVisible()` — off-screen portals pass visibility checks.
- Measure before editing counts; update §1 in the same change as new tests.
