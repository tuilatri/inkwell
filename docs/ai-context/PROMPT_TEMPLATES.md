# PROMPT_TEMPLATES — inkwell

> Templates reused when prompting agents. Keep the original format.

## Task Execution
| Template | Use when | Content |
|---|---|---|
| Standard task | Any code/doc change | `Read: <files>` line → classify per Workflow Contract → **if non-trivial: create plan docs then STOP for approval** → after approval implement exactly the plan → verify with exact gates → fix until green → stop. Propose a commit message in the report, but commit/push only if explicitly asked in that turn — push/PR/merge does NOT imply commit permission; ask first when changes are uncommitted. Language: chat Vietnamese, docs/code English. |
| Casual "làm này/làm kia" | Owner speaks loosely | Apply `AGENTS.md` Workflow Contract: prefer planning when in doubt; "plan"/"làm theo quy trình" forces a plan, "làm luôn" forces immediate action. |
| Doc Trigger update | Touching API/service/component/tests | Name the matching `docs/ai-context/` file from AGENTS.md before editing; update it in the same change (numbers measured, never guessed). |
| Bug fix | Something fails | Reproduce → read `KNOWN_TRAPS.md` first → fix root cause → add regression test (unit or E2E layout assertion) → record a new trap only if genuinely new. |
| Verify before claim | Before saying "done" | Run backend pytest + frontend Vitest/build + relevant E2E + `node scripts/verify.mjs`; quote actual output, never assert from memory. |

## Review / planning
| Template | Use when | Content |
|---|---|---|
| Plan | ≥3 files or ≥5 changes | Mandatory `drafts/plans/<MMDDYY>_<n>_<status>/implementation_plan.md` + `task.md`, immutable task IDs, verification last. |
| UI critique | Visual/UX work | Load `impeccable`; decide Operate/Read mode; check contrast, focus, states, responsive; run `detect.mjs` once; batch fixes. |
