# UI_UX_RULES — inkwell

> Component conventions + design rules for `novel_reader/frontend/` (full details in FRONTEND_MAP.md).

## Component Library
- Tailwind CSS v4 + shadcn/ui `new-york`, Radix primitives; `lucide-react` icons; one primary component per file (`components/ui/` and `components/app/`).
- `Button` uses `React.forwardRef` — Radix `asChild` triggers need a real DOM ref.
- Dark-only theme "Night reading desk" (graphite `#15130f`, card `#1e1b16`, amber `#e0a458`); tokens in `src/index.css`, dark class set by `ThemeProvider` (`defaultTheme="dark"`).

## Patterns
- Library: names-only cards, skeleton loading, actionable empty/error states, EN/VI tabs with VI default; chapter TOC shows **names only** (no content/snippet), one horizontal scrollbar for the whole list, `…` overflow on long names, sticky bookmark marker for already-read chapters.
- Login: password field has an Eye/EyeOff toggle with `aria-label` + `aria-pressed`.
- Reader: prev/next buttons in the sticky toolbar (bottom row kept), progress bar fused to that toolbar so it never scrolls away; virtualized chapter list (bounded DOM for 1.700+ rows, zero-height fallback), font/line-height sliders, reading position saved with debounce, mobile `Sheet`.
- Predictive search: suggestions on open, 180 ms debounce, accent-insensitive prefix, highlighted matches, spinner; empty state only after a real miss.
- Affordances: pointer cursor on interactive elements, focus ring on buttons/links/tabs, border-only focus on inputs, `focus-within:border-accent` on the palette wrapper.
- Motion: overlay fade, dialog scale (independent `scale` property), sheet slide, card lift, content rise; `prefers-reduced-motion` disables all.
- Browser scrollbars are themed from the palette — including `::-webkit-scrollbar-corner`, so the junction of the vertical and horizontal scrollbars never renders a white block.

## Anti-patterns (forbidden)
- Covers/images in the library (owner requirement: text only).
- Kicker/eyebrow labels above headings, gradient text, nested cards, icon-only controls without `aria-label`.
- Fixed floating buttons that overlap navigation (use normal flow rows).
- Overlay keyframes that set `transform` (breaks Radix Popper positioning), or `[role="combobox"]:focus-visible` outlines that spill outside inputs.
- localStorage for tokens (theme key only), light theme, untested portal positioning (`toBeVisible` alone is not enough).
