# AGENTS.md — inkwell

> Constitution for every agent working in this repo. Copy the principles; keep them current with the code.

<!-- GitNexus: run `npx gitnexus analyze` once code exists — this block is auto-generated. -->

---

# Project Source of Truth

- **Read first:** `docs/ai-context/README.md` — index of all context docs.
- **Read before editing:** per the Doc Trigger table below — one condition, two directions (read before + update after).
- **`drafts/` is gitignored and NOT a source of truth.**
- **`HOW_TO_RUN.txt` contains real credentials** (gitignored) — read it to check config, never quote its values.

---

# Pre-Task Checklist (mandatory, in order)

1. **Re-read AGENTS.md** — refresh rules
2. **Read `docs/ai-context/BEHAVIORAL_GUIDELINES.md`** — principles + skill selection
3. **Read `docs/ai-context/KNOWN_TRAPS.md`** — avoid known pitfalls
4. **Check the Doc Trigger table** — read the matching doc files. Declare it in the first line of your reply.
5. **Before EVERY edit** — run impact analysis on the target symbol
6. **Large task (≥3 files, ≥5 changes)** — create a hierarchical plan
7. **Before committing** — run detect_changes() to confirm scope
8. 🔴 **Tasks must have immutable IDs** (`P2-9`, `PR #7`) — never "item N"

---

# Plan & Task Documents

**MANDATORY**: create `implementation_plan.md` + `task.md` in `drafts/plans/<MMDDYY>_<n>_<status>/`.

# Commit Message Convention

- Prefixes: `feat:` `fix:` `refactor:` `chore:` `style:` `docs:` `test:` `perf:` + scope
- Subject ≤ 72 chars, English

# Language
- Chat with the user: Vietnamese
- Code, identifiers, technical docs: English

---

# Standing Rules

1. **`drafts/` is gitignored, not a source of truth.** Need context → read `docs/ai-context/`.
2. Read the matching doc per the Doc Trigger before editing.
3. Details: `.agent/rules/` — read only when the task needs it.
4. Plan/task docs: `drafts/plans/<MMDDYY>_<n>_<status>/`.
5. End of task: report status + propose a commit message.
6. **Test gate:** run the project's verify gate (declared in Quick Facts). Current counts live in `docs/ai-context/TESTING_GUIDE.md` §1 — measure, never guess.
7. **Never commit secrets.** `.env`, `.env.*`, credential files — gitignored. Never quote values.
8. **Never commit build output / dependencies / runtime data.**

---

# Doc Trigger — one condition, two directions

| Task touches | Read **before** editing | Update **when changed** |
|---|---|---|
| any endpoint in `novel_reader/backend/app/api/` | `docs/ai-context/API_MAP.md` | ✔ |
| any service in `novel_reader/backend/app/services/` | `docs/ai-context/ARCHITECTURE.md` §2, §5 | ✔ |
| any route/page in `novel_reader/frontend/src/pages/` | `docs/ai-context/FRONTEND_MAP.md` §1 | ✔ |
| anything in `novel_reader/frontend/src/components/` | `docs/ai-context/FRONTEND_MAP.md` §2–§5 | ✔ |
| anything in `comix_downloader/` (scraper) | `docs/ai-context/MODULE_MAP.md` + `ARCHITECTURE.md` §6 | ✔ |
| backend tests or pytest config | `docs/ai-context/TESTING_GUIDE.md` | ✔ |
| repo structure, adding/removing apps | `docs/ai-context/MODULE_MAP.md` | ✔ |
| `HOW_TO_RUN.txt`, `.env*` | Standing Rules 7 | ✔ |
| add/change gates, claims | `kit.config.json` (+ `kit.config.schema.json`) | ✔ |
| CI/test/ORM traps | `docs/ai-context/KNOWN_TRAPS.md` | — |
| Skill selection / principles | `docs/ai-context/BEHAVIORAL_GUIDELINES.md` | — |

**Declare:** the first line of every reply must be `Read: <file list>`.

**Authority:** docs describe the **existing code**. When docs contradict code ⇒ **code is right, docs are wrong.**

---

# Quick Facts — measured 2026-11-17

| | |
|---|---|
| Apps | `comix_downloader/` — Python scraper, 10 files / 2.880 lines · `novel_reader/backend/` — FastAPI, 33 files / 1.484 lines · `novel_reader/frontend/src/` — React/Vite/TS, 58 files / 1.662 lines |
| Backend entry | `cd novel_reader/backend && .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000` |
| Frontend entry | `cd novel_reader/frontend && npm run dev` (`:5173`, `/api` proxied to `:8000`) |
| DB | PostgreSQL 18 — two empty-at-setup DBs (TEST used by default, PRODUCTION only on request); Alembic `0001_initial` + `0002_source_dir_and_soft_delete`; tables created on both |
| Auth | Single admin seeded from `.env` on empty `admin_users`; argon2id password; JWT in `nr_access`/`nr_refresh` HttpOnly cookies (`jti` in DB); CSRF header on state-changing routes |
| Agent roles | `.claude/agents/` — 10 role cards + README, native frontmatter, body referencing `docs/ai-context/` |
| Verify | `node scripts/verify.mjs` — gates in `kit.config.json` (pytest / vitest / build); `node scripts/doc-truth.mjs` checks claims; `--fast` skips `slow`, `--list` lists gates |
