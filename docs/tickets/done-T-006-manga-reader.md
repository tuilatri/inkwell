# T-006 — Manga/Manhwa reading mode

Spec: SPEC-manga-reader · Labels: reader, manga, feature
Status: open (rename to doing- at implementation start, done- after green verification)

## Why
~25.000 scraped images under `drafts/Manhwa/` are invisible to the reader, which only scans text.

## What
- Alembic 0004: `chapters.kind`, `reading_state.page_index`.
- `MANHWA_ROOT` config + stat-only image scanner; reuse VI/EN variants.
- Pages manifest + authenticated media endpoint; lazy MangaReader with page progress.
- Docs + tests per SPEC.

## Done when
- [ ] G1–G8 of `drafts/plans/111724_4_draft/` checked
- [ ] All gates green, production untouched, no commit without explicit request
