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
6. **Large task (≥3 files, ≥5 changes)** — create a hierarchical plan (see Workflow Contract; plan-first applies to all non-trivial work)
7. **Before committing** — run detect_changes() to confirm scope
8. 🔴 **Tasks must have immutable IDs** (`P2-9`, `PR #7`) — never "item N"

---

# Plan & Task Documents

**MANDATORY**: create `implementation_plan.md` + `task.md` in `drafts/plans/<MMDDYY>_<n>_<status>/`.

`<status>` lifecycle (owner-approved 2026-11-17):
- `draft` — new plan, work in progress.
- `done` — every task in `task.md` is `[x]` and its verification passed.
- `cancelled` — stopped by owner decision; append `Status: cancelled — <reason>` to `task.md` and leave unfinished boxes unchecked.

Tick `[x]` in `task.md` as each task finishes, not in one batch at the end. Rename the folder to `_done` when the last task verifies green, or to `_cancelled` when the owner stops it.

# Workflow Contract — owner-approved 2026-11-17

For every **non-trivial** request, follow this loop in order:

1. **Classify** — any request that creates/changes code, config, docs, skills, or touches ≥3 files is non-trivial. Exempt: questions, read-only inspection/reports, and a clearly labelled one-line typo fix when the owner says "làm luôn".
2. **Plan first** — before any edit, create `implementation_plan.md` + `task.md` in `drafts/plans/<MMDDYY>_<n>_<status>/` with immutable IDs, exact files/interfaces and verification steps. Then **STOP** in the same turn — do not implement yet. Wait for the owner's approval.
3. **Execute after approval** — implement exactly the approved plan; surface any deviation before making it. When executing a ticket from `docs/tickets/`, rename `open-…` → `doing-…` at start and `doing-…` → `done-…` only after verification is green; link the plan to the ticket via a `Ticket:` line. **State lives in the filename — never change it by editing the file body.**
4. **Verify & repair** — run the gates relevant to the scope (pytest / vitest / build / Playwright E2E / `node scripts/verify.mjs` / `node scripts/doc-truth.mjs`). On any failure, fix until all green; quote real command output — never claim success from memory.
5. **Stop clean** — when verification is green, stop. **Do NOT commit or push unless the owner explicitly asks for commit/push in that same turn.** A push/PR/merge request does **NOT** imply commit permission — commit requires the owner's explicit word (e.g. "commit") in that turn. If changes are uncommitted when push is requested, stop and ask for commit permission instead of committing.
6. **Ambiguity guard** — if a casual request could be trivial or non-trivial, prefer planning. The owner can force it with "plan" / "làm theo quy trình", or force immediate action with "làm luôn".

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
9. **No implicit commit/push** — only when the owner explicitly asks in the current turn (see Workflow Contract step 5). Push/PR/merge ≠ commit permission: if changes are uncommitted, ask first.

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
| `docs/tickets/` or `docs/specs/` | `docs/agents/issue-tracker-local.md` (state = filename rename) | ✔ |
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
| Apps | `comix_downloader/` — Python scraper, 10 files / 2.880 lines · `novel_reader/backend/` — FastAPI, 38 files / 1.953 lines · `novel_reader/frontend/src/` — React/Vite/TS, 60 files / 1.964 lines |
| Backend entry | `cd novel_reader/backend && .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000` |
| Frontend entry | `cd novel_reader/frontend && npm run dev` (`:5173`, `/api` proxied to `:8000`) |
| DB | PostgreSQL 18 — two empty-at-setup DBs (TEST used by default, PRODUCTION only on request); Alembic `0001_initial` … `0006_manga_clean_title` (6 revisions); tables created on both |
| Auth | Single admin seeded from `.env` on empty `admin_users`; argon2id password; JWT in `nr_access`/`nr_refresh` HttpOnly cookies (`jti` in DB); CSRF header on state-changing routes |
| Agent roles | `.claude/agents/` — 10 role cards + README, native frontmatter, body referencing `docs/ai-context/` |
| Verify | `node scripts/verify.mjs` — gates in `kit.config.json` (pytest / vitest / build); `node scripts/doc-truth.mjs` checks claims; `--fast` skips `slow`, `--list` lists gates |
