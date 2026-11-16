# PROMPT_TEMPLATES — inkwell

> Templates reused when prompting agents. Keep the original format.

## Task Execution
| Template | Use when | Content |
|---|---|---|
| Standard task | Any code/doc change | `Read: <files>` line → state assumptions → plan (if ≥3 files) → implement surgical changes → verify with exact commands → report status + commit message. Language: chat Vietnamese, docs/code English. |
| Doc Trigger update | Touching API/service/component/tests | Name the matching `docs/ai-context/` file from AGENTS.md before editing; update it in the same change (numbers measured, never guessed). |
| Bug fix | Something fails | Reproduce → read `KNOWN_TRAPS.md` first → fix root cause → add regression test (unit or E2E layout assertion) → record a new trap only if genuinely new. |
| Verify before claim | Before saying "done" | Run backend pytest + frontend Vitest/build + relevant E2E + `node scripts/verify.mjs`; quote actual output, never assert from memory. |

## Review / planning
| Template | Use when | Content |
|---|---|---|
| Plan | ≥3 files or ≥5 changes | Mandatory `drafts/plans/<MMDDYY>_<n>_<status>/implementation_plan.md` + `task.md`, immutable task IDs, verification last. |
| UI critique | Visual/UX work | Load `impeccable`; decide Operate/Read mode; check contrast, focus, states, responsive; run `detect.mjs` once; batch fixes. |
