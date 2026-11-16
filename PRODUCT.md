# PRODUCT — Inkwell (ground truth, 2026-11-17)

> Product facts for agents. No invented customers, prices, or claims — everything here is traceable to the code in this repo.

## What this product is
A solo-developer repo that combines two small products:

1. **Comix.to scraper** (`comix_downloader/`) — Python CLI + GUI that walks a Comix.to series with real Chrome, handles pagination and scanlation groups (`/groups/NNNN`), and downloads chapter text/images to disk. Imported from `D:\bato-downloader\src\comix_downloader`; that source stays read-only.
2. **Inkwell Novel Reader** (`novel_reader/`) — private, single-admin web app that reads `.txt` novels from `drafts/Novel/` (the scraper's output area), with a React/Vite SPA, FastAPI backend and PostgreSQL. Features: login, library (titles only), EN/VI variants, reading position, predictive search.

## Audience
- Owner / solo developer. Chat language Vietnamese; code, identifiers and technical docs English.

## Jobs to be done
- Scrape a chosen series/group/chapter reliably into `drafts/Novel/` without touching the original project.
- Log in, see which novels exist on disk, switch language, read chapters comfortably, and resume at the same position later.
- Find a chapter by partial/accentless title through predictive search.

## Constraints (non-negotiable)
- `drafts/Novel/` and `.chrome_profile/` are gitignored runtime data — never committed.
- Source `.txt` files stay on disk; DB stores only metadata, FTS index and reading state.
- Single admin seeded from untracked `.env`; JWT in HttpOnly cookies, no localStorage tokens; CSRF on mutations.
- Dark-only UI; no covers/images in the library (owner requirement).
- Two Postgres DBs (TEST default, PRODUCTION only on explicit request). No Docker yet.
- Anti-extension/anti-scrape is best-effort; public deployment should add TLS + Tailscale/IP allowlist.

## What success looks like
- `node scripts/verify.mjs` → all gates PASS; `node scripts/doc-truth.mjs` → 0 FAIL.
- Backend 31 pytest · frontend 22 Vitest · 2 Playwright E2E (login → library → EN/VI → read → scroll → refresh → search).
- Docs in `docs/ai-context/` describe the code, with numbers measured (never guessed).
