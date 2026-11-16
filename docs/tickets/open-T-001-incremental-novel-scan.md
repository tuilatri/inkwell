# T-001 — Incremental novel scan

Spec: SPEC-novel-scanner
Blocks: —
Blocked by: —
Labels: reader, performance

## Why
Backend startup rescans ~5.300 txt files / 90 MB, costing 40–60 s before the reader API is ready. The stored `chapters.file_mtime` is unused.

## What
- Add a cheap path+mtime fingerprint to `app/services/scanner.py`; skip upsert/FTS rebuild when it matches the last completed `scan_log`.
- Re-scan only changed novel/variant folders; keep soft-delete and warning behavior.
- Keep `POST /api/admin/rescan` as the full-scan escape hatch.

## Done when
- [ ] Warm start < 5 s measured and recorded in `ARCHITECTURE.md` §7
- [ ] Add/rename/delete chapter covered by a regression test; reading state survives
- [ ] Backend suite green; `TESTING_GUIDE.md` §1 updated if tests were added
- [ ] Rename this file `doing-T-001-...` when work starts, then `done-T-001-...` (state = filename, never edit the body for state)
