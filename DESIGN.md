# DESIGN — Inkwell Novel Reader (ground truth from shipped code, 2026-11-17)

> This is the durable visual world of the web app. It was documented from the built UI in `novel_reader/frontend/src/`, not written as a wish list. Details: `docs/ai-context/FRONTEND_MAP.md`, `UI_UX_RULES.md`.

## Visual world: "Night reading desk"
A quiet, warm dark surface for reading at night — not a generic near-black neon dashboard. Graphite canvas, parchment-tinted reading card, one amber accent reserved for primary action and reading progress. Mono numerals for chapter numbers; serif body for chapter text.

## Tokens (source: `src/index.css`)
- `--background: #15130f` (warm graphite) · `--card: #1e1b16` (parchment-tinted) · `--foreground: #ece6da`
- `--muted-foreground: #b3a894` · `--border / --input: #3a342a` · `--accent: #e0a458` · `--accent-foreground: #1a140c` · `--destructive: #e2846f`
- Radius `--radius: 0.625rem`; 4px spacing rhythm; 1px hairline borders; shadows with real offset + soft blur.

## Typography
- UI chrome: IBM Plex Sans (system fallback). Chapter body: Newsreader serif, 1.0625rem default with adjustable size 14–24 px and line-height 1.5–2.4. Chapter numbers: mono/tabular.
- Tracking floor -0.02em on headings; clear scale steps (display 3xl / heading xl / body 15px / caption 14px). Body measure capped at 70ch in the reader.

## Component language
- shadcn/ui `new-york` + Radix primitives, Tailwind v4. One primary component per file. Buttons with real hover/active/focus states; `Button` forwards refs for Radix `asChild`.
- Selection, caret, scrollbar and focus rings are themed from the palette (no browser defaults).

## Surface patterns
- **Login**: centered branded card, Label + Input + primary Button, inline Alert errors, pending spinner; minimal navbar (brand only) + footer.
- **Library**: sticky navbar (brand link, ⌘K search, account dropdown) → heading → novel Card grid (titles only) → selected novel's EN/VI Tabs + virtualized chapter list → footer. Skeleton while loading; actionable empty state.
- **Reader**: navbar + sticky toolbar (back, title, font/line-height sliders, search, chapter-list toggle) + reading-progress bar; serif text card; prev/next row in normal flow; mobile chapter list in a right Sheet; toast on saved position.

## Motion & interaction
- One vocabulary: overlay fade (180 ms), dialog scale via independent `scale` property (200 ms), sheet slide (240 ms), card lift (180 ms), content rise (260 ms), exponential ease-out.
- `prefers-reduced-motion` disables all. Keyboard: ⌘K search, J/K or ←/→ chapters, Esc closes overlays. Pointer cursor on every interactive control; focus ring for buttons/links/tabs, border-only focus for inputs (no outline spilling outside the search box).

## Responsive & accessibility
- Desktop two-column library/reader; mobile stacks, chapter list moves to Sheet. Touch targets ≥44 px. WCAG AA contrast (≥4.5:1 body). Focus order and aria labels verified by E2E and audit.

## Anti-patterns (from KNOWN_TRAPS)
- No fixed floating buttons overlapping navigation; no keyframe `transform` on positioned dialogs; no `[role="combobox"]:focus-visible` outline outside inputs; no substring numeric filter ("128" must not match 1128); no localStorage tokens; no covers/images in library; no nested cards or gradient text.
