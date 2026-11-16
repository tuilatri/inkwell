# ROUTER — pre-task bootstrap (inkwell)

## Loading order
1. `AGENTS.md` — contract, Pre-Task Checklist, Doc Trigger, Quick Facts.
2. `docs/ai-context/README.md` → the matching doc from the table below (read before edit, update after change).
3. `docs/ai-context/KNOWN_TRAPS.md` — always, before fixing anything.
4. `docs/agents/triage-labels.md` — only when creating/renaming a ticket in `docs/tickets/`.

## Task type → docs / skills
| Task type | Read | Skill |
|---|---|---|
| API endpoint / auth | `API_MAP.md`, `ARCHITECTURE.md` §4–§5 | `api-patterns` |
| Backend service / DB | `ARCHITECTURE.md` §2–§3, `MODULE_MAP.md` | `python-patterns`, `database-design` |
| Frontend component / UX | `FRONTEND_MAP.md`, `UI_UX_RULES.md` | `impeccable`, `react-patterns`, `tailwind-patterns` |
| Scraper change | `MODULE_MAP.md`, `ARCHITECTURE.md` §6, `SKILL-SOURCES.md` | `clean-code` |
| Tests / bug fix | `TESTING_GUIDE.md`, `KNOWN_TRAPS.md` | `tdd`, `systematic-debugging`, `verification-before-completion` |
| Plan / large change | `PROMPT_TEMPLATES.md` | `writing-plans`, `plan-writing` |

## General rules
Commit convention, plan folder (`drafts/plans/<MMDDYY>_<n>_<status>/`), language and standing rules live in `AGENTS.md` — reference them, never duplicate here. First line of every reply: `Read: <files>`.
