# Issue Tracker — Local Markdown Mode

> Private repo / solo dev — want a tracker without an external service: the entire
> ticket lifecycle lives in git, as plain markdown.
>
> The engineering skills (to-spec / to-tickets / implement / implement-spec — installed
> via `npx skills@latest add mattpocock/skills -a claude-code -y`) follow exactly this convention.

- **Location**: `docs/tickets/` — one file per ticket, named `T-NNN-slug.md`
- **Ticket states** (filename prefix): `open-` → `doing-` → `done-` — changing state = **RENAME the file**, do not edit its content
- **Blocking edges**: declared in the ticket body as `Blocks: T-xxx` / `Blocked by: T-xxx`
- **Specs**: `docs/specs/SPEC-slug.md` — tickets link back via a `Spec: SPEC-slug` line
- Creation rule: tickets and specs are written in English (repo doc convention)

## Current mode

- Tracker tool: none (local markdown only)
- Ready for: to-spec → to-tickets → implement-spec pipeline

## Example ticket

`docs/tickets/doing-T-004-incremental-novel-scan.md`:

````markdown
# T-004 — Incremental novel scan

Spec: SPEC-novel-scanner
Blocks: T-005
Blocked by: T-002

## Why
Startup rescans ~5.300 txt files / 90 MB, costing 40–60 s before the API is ready.

## What
- Use the stored `chapters.file_mtime` to skip unchanged files in `app/services/scanner.py`
- Keep `POST /api/admin/rescan` as the full-scan escape hatch
- Publish measured startup time in `docs/ai-context/ARCHITECTURE.md` §7

## Done when
- [ ] Cold start unchanged; warm start < 5 s measured
- [ ] Backend tests still green; TESTING_GUIDE §1 updated if tests were added
````
