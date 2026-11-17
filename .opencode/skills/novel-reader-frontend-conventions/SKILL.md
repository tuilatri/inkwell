---
name: novel-reader-frontend-conventions
description: Hard rules for novel_reader/frontend/src/** — use when building or changing React/Vite/shadcn components, dark-theme tokens, virtualized chapter lists, command palette, focus/motion, reading progress, or frontend tests. Also use when editing FRONTEND_MAP.md or UI_UX_RULES.md.
metadata:
  scope: novel_reader/frontend/src/**, docs/ai-context/FRONTEND_MAP.md, docs/ai-context/UI_UX_RULES.md
---

# Novel reader frontend conventions

Rule 0 — **One component per file.** `src/components/ui/` holds shadcn primitives; `src/components/app/` holds one-responsibility wrappers. Compound parts (CardHeader, TabsTrigger) stay with their family. Why: the owner explicitly required a dedicated file per component.

Rule 1 — **Button must forward refs.** `React.forwardRef<HTMLButtonElement, ButtonProps>` — Radix `asChild` triggers (dropdown/tooltip/sheet) need a real DOM ref, otherwise Popper positions overlays at `translate(0,-200%)` off-screen. Verify popups with `boundingBox().y > 0`, not only `toBeVisible()`.

Rule 2 — **Dark-only, token-driven.** Tailwind v4 `@theme inline` + shadcn `new-york`; graphite/card/amber tokens in `src/index.css`; no light theme, no covers in library. Chapter body is serif (Newsreader), numerals mono, chrome IBM Plex Sans. Example: `UI_UX_RULES.md`.

Rule 3 — **Search is predictive.** Suggestions on open (empty `q`), 180 ms debounce, accent-insensitive prefix, highlighted matches, spinner; show the empty state only after a real miss. The cmdk input must not get an outline that spills outside the box — focus shows via wrapper `focus-within:border-accent`.

Rule 4 — **Large lists are virtualized.** `@tanstack/react-virtual` for chapters (~1.700 rows); bounded DOM regardless of corpus size. Numeric filter matches exact chapter numbers ("128" ≠ 1128). Example: `virtual-chapter-list.tsx`.

Rule 5 — **Motion is one vocabulary.** Overlay fade, dialog `scale` (independent CSS property — never keyframe `transform`, it breaks positioning), sheet slide, card lift, content rise, `prefers-reduced-motion` respected. Pointer cursor on interactive elements, focus ring on buttons/links/tabs, border-only focus on inputs.

Rule 6 — **Keep tests and docs in lockstep.** 22 Vitest + 2 Playwright E2E; jsdom needs `src/test-setup.ts` shims. Update `FRONTEND_MAP.md`/`UI_UX_RULES.md` in the same change, and `TESTING_GUIDE.md` §1 after count changes.
