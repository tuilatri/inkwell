# SPEC — Incremental novel scan

## Problem
On every backend start, `app/services/scanner.py` re-reads the whole corpus
(~5.300 `.txt` files, ~90 MB). Measured cold/warm startup: 40–60 s before the
API accepts requests. The stored `chapters.file_mtime` is currently written but
never used to skip unchanged files.

## Goal
Warm start of the reader API in < 5 s without changing scan correctness for
new, renamed or removed files.

## Behavior
1. On startup, hash the set of relative `.txt` paths + `mtime` under
   `drafts/Novel/` (cheap directory walk, no file reads).
2. If the set is unchanged from the last completed `scan_log`, skip the DB
   upsert and FTS rebuild entirely.
3. If changed, re-scan only novel/variant folders whose file set changed;
   unchanged chapters keep their rows, reading state and search index.
4. `POST /api/admin/rescan` always forces a full scan and a fresh FTS rebuild.
5. Soft-delete semantics (`active=false` for missing files) stay unchanged.

## Acceptance criteria
- [ ] Cold start (empty DB) still scans the full corpus and indexes all active chapters.
- [ ] Warm start with no file changes performs no per-file reads (measured) and completes < 5 s.
- [ ] Adding, renaming and deleting a chapter updates `chapters`, `scan_warnings` and FTS correctly.
- [ ] `reading_state` of a temporarily missing chapter survives when the file returns.
- [ ] Backend tests stay green; `TESTING_GUIDE.md` §1 updated if tests were added.

## Out of scope
Docker, file watching while the server runs, moving text into PostgreSQL.
