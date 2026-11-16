---
name: comix-scraper-conventions
description: Hard rules for comix_downloader/** — use when changing the imported Comix.to scraper CLI/GUI, pagination detectors, chapter parsing, group filtering, Chrome session handling, or its tests. Also use when touching drafts/Novel/ output consumed by the reader.
metadata:
  scope: comix_downloader/**, drafts/Novel/**
---

# Comix scraper conventions

Rule 0 — **The original source is read-only.** `D:\bato-downloader\src\comix_downloader` was the import source; all edits happen only in this repo's `comix_downloader/`. Why: the external project is not ours to change. Example: patch `comix_downloader/gui.py`, never the D:\ copy.

Rule 1 — **Entry points are package-style.** Run `python -m comix_downloader gui|download` from the parent of the package; relative imports inside modules are intentional. Why: the folder was renamed from `comix-downloader` to fix that import contract. Example: `--group /groups/11494 --range 3-3 -o .`.

Rule 2 — **Groups are hrefs, never display names.** `--group` takes `/groups/NNNN`; chapter numbers are positions in the *filtered* list, not site chapter numbers. Why: two groups publish the same chapter number. Example: list first, then download `3-3`.

Rule 3 — **Text is the product; images are runtime.** The reader consumes only `.txt` under `drafts/Novel/<novel>/chapters_{vi,en}/`; `_index.txt`, `.json` and images are skipped by the scanner. Never commit `drafts/` or `.chrome_profile/`. Example: output chapter text into the current folder, then let the scanner pick it up.

Rule 4 — **Chrome profile is disposable session data.** `.chrome_profile/` is auto-created under the package dir (~100–200 MB, cookies/history); it is gitignored, never committed, and cleanup is available via `cleanup_chrome_profile()`. Why: session leakage + repo bloat.

Rule 5 — **Respect the site and measure failures.** Real Chrome + stealth is anti-detection, not permission: use modest concurrency, retry after transient 0-chapter walks (observed once), and log warnings instead of crashing. Example: `time.sleep(10)` page load, max-pager ceiling.

Rule 6 — **Tests before claims.** `tests/test_manga_info.py` / `test_search.py` exercise live parsing; network may be unavailable, so report skips honestly. Never claim a scrape succeeded without checking downloaded file count and bytes.
