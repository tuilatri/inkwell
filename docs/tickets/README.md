# Tickets — local markdown tracker

One file per ticket, named `T-NNN-slug.md`. States are **filename prefixes**:
`open-` → `doing-` → `done-`. Change state by **renaming the file**, not editing its body.

- Blocking edges: `Blocks: T-xxx` / `Blocked by: T-xxx` in the ticket body.
- Specs live in `docs/specs/SPEC-slug.md`; tickets link back with `Spec: SPEC-slug`.
- Language: English (repo doc convention). Labels: see `docs/agents/triage-labels.md`.

No tickets yet — create T-001 when starting the next task (see `docs/agents/issue-tracker-local.md`).
