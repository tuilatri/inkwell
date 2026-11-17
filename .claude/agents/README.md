# Agent roles — inkwell

The 10 role files in this directory are ready to use — no copying needed. All
per-role markers were filled on 2026-11-17 to match the actual two-app repo:

| Role | Verify command (in its "Verify" section) |
|---|---|
| be-engineer.md | `cd novel_reader/backend && .\.venv\Scripts\python.exe -m pytest -q` |
| fe-engineer.md | `cd novel_reader/frontend && npx vitest run && npm run build` |
| db-engineer.md | `cd novel_reader/backend && .\.venv\Scripts\alembic.exe current` |
| devops-ci.md | `node scripts/verify.mjs` (repo root) |
| mobile-engineer.md | N/A — no native mobile app; Playwright mobile viewport E2E |

Owned scopes were updated from the scaffold's `backend/**` / `frontend/**` to
`novel_reader/backend/**` and `novel_reader/frontend/**`. `mobile-engineer` is
kept only for responsive checks. Any remaining `{{...}}` is an intentional
fill-in marker — none should remain in this directory.

Delete roles you don't use; add domain-specific roles following the same
frontmatter + section pattern (Required Reading / Owned Scope / Verify /
Escalate / Never Do / Handover Format).
