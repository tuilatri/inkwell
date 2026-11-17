# GLOSSARY — inkwell

> Ubiquitous language of the domain. Definitions ≤ 2 lines; every term is traceable to code.
> The `domain-modeling` + `grill-with-docs` skills feed this file.

| Term | Definition |
|---|---|
| `comix_downloader` | Imported Python scraper (`comix_downloader/cli.py`, `gui.py`) for Comix.to. Its source project is read-only; all edits happen in this repo. |
| scanlation group | Translator identity of a chapter, expressed as `/groups/NNNN` href. `--group` filters by href, never by display name — two groups can publish the same chapter number. |
| chapter | One `.txt` file under `drafts/Novel/<novel>/chapters_{vi,en}/`, at any depth — flat `Chapter_001.txt` or folder `Chapter 1/text.txt`. Images/index files are not chapters. |
| `drafts/Novel/` | Gitignored content root: scraper output and scanner input. Never committed; the scanner reads it, the DB only stores derived metadata. |
| variant | A novel's language row (`novel_id` + `lang` = `vi` or `en`) from `app/db/models.py`; the reader shows EN/VI tabs with VI as default. |
| `chapter_search` | Postgres table holding `to_tsvector('simple', unaccent(text))` + GIN index; rebuilt by `app/services/search_index.py` for accent-insensitive prefix search. |
| `scan_log` / `scan_warnings` | Audit tables written by every scan: counts plus duplicate-number / missing-file warnings. Scanning is observable, never silent. |
| `reading_state` | Per-user, per-chapter scroll offset saved with a 1 s debounce; soft-deleted chapters keep this row so a returning file resumes correctly. |
| admin seed | First-run creation of the single admin from untracked `.env`, only when `admin_users` is empty; a password change through the UI voids the env credentials. |
| `token_sessions` | Table of JWT `jti` rows (kind, expiry, `revoked_at`) backing logout and refresh rotation — tokens are revocable, not stateless-only. |
| Chrome profile | `.chrome_profile/` — disposable browser session (~100–200 MB cookies/history) created by the scraper; gitignored, cleaned by `cleanup_chrome_profile()`. |
| verify gate | A command declared in `kit.config.json` and run by `scripts/verify.mjs`; `doc-truth.mjs` checks numeric/existence claims, and the pre-commit hook runs the `--fast` subset. |
