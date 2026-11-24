# FRONTEND_MAP — inkwell

## 1. Routes
| Route | File | Lines | Notes |
|---|---|---:|---|
| `/login` | `novel_reader/frontend/src/pages/Login.tsx` | 8 | Composes `LoginForm`; dark branded card |
| `/` | `novel_reader/frontend/src/pages/Library.tsx` | 116 | Library grid (titles only), EN/VI tabs, virtualized chapter list, ⌘K |
| `/read/:chapterId` | `novel_reader/frontend/src/pages/Reader.tsx` | 152 | Reader with font controls, progress, shortcuts, mobile sheet |

## 2. Key components
- `components/ui/` — 483 lines, 24 files: shadcn/new-york primitives (Radix-based). One primary component per file: button, input, label, card, badge, separator, skeleton, alert, spinner, empty, kbd, typography, tooltip, progress, tabs, dropdown-menu, scroll-area, slider, dialog, sheet, command, sonner, switch, toggle-group. Compound parts (CardHeader, TabsTrigger, …) live with their family.
- `components/app/` — 16 files, one responsibility per file: theme-provider, app-header (navbar; brand links home, search, account dropdown with "Đăng xuất"; `minimal` variant for login), app-footer, login-form (password Eye/EyeOff toggle), novel-card, variants-tabs, search-command, chapter-filter, virtual-chapter-list, reader-toolbar, reader-view, mobile-chapter-sheet, keyboard-shortcuts, empty-state, error-state. Navbar + footer appear on login/library/reader; reader toolbar sticks below the navbar (`top-16`) and carries the prev/next chapter buttons plus the progress bar at its bottom edge. `reading-progress.tsx` was removed — the progress bar lives inside the sticky toolbar now.
- Chapter rows: **one** horizontal scrollport for the whole list (container `overflow-auto` + wide inner surface); rows have fixed width and `truncate` long names with `…`; **no chapter content/snippet** in any list (home TOC, reader aside, mobile sheet); sticky Bookmark icon marking `visited` chapters stays visible while scrolling; virtualized with a bounded first-page fallback for zero-height containers.
- Manga mode: `NovelCard` shows a small `Novel`/`Manhwa` badge (titles stay plain, no ` (manga)` suffix). `MangaReader` renders the **whole chapter** as one vertical list of lazy-loaded images (`width`/`height` attributes reserve layout so saved-page restore works); `N/M` counter tracks the most-visible image via IntersectionObserver, zoom fit/actual applies to all images, ←/→ scroll one image into view; progress writes `page_index` = last-visible page, text chapters keep pixel `scroll_pos`. Chapter rows show a "tranh" badge for `kind='images'`; a missing VI variant shows a friendly empty TOC.
- Reader lists receive `activeId` (current chapter): on mount/open and on navigation the list calls `scrollToIndex(align:center)` and marks the row with `aria-current="location"` + amber background/weight; Library TOC passes none.

## 3. UI conventions
- Single dark theme "Night reading desk": warm graphite `#15130f`, parchment-tinted card `#1e1b16`, one amber accent `#e0a458`; tokens in `src/index.css` (`@theme inline`).
- Tailwind CSS v4 via `@tailwindcss/vite`; shadcn style `new-york` (`components.json`); lucide icons; serif (Newsreader) for chapter text, mono numerals for chapter numbers.
- No covers/images in library — titles only (owner requirement).
- Every async path has loading skeletons, empty state, or error alert; toasts for saved position.
- Keyboard: ⌘K search; J/K or ←/→ chapter nav; Esc closes overlays. Mobile: chapter list in a `Sheet`.
- Search is predictive: suggestions on open (empty query), accent-insensitive prefix/substring in Postgres (`unaccent(...) ILIKE` + FTS), 180 ms debounce, matched text highlighted, spinner/empty state gated on loading.
- Affordances: pointer cursor on all interactive controls, focus ring on buttons/links/tabs, border-only focus on inputs (including cmdk combobox — no outline spilling outside); the command palette wrapper uses `focus-within:border-accent`. Motion vocabulary: overlay fade, dialog scale, sheet slide, card lift, content rise; `prefers-reduced-motion` respected.
- `Button` uses `React.forwardRef` — required by Radix `asChild` (dropdown/tooltip/sheet triggers) so Popper can anchor overlay content.

## 4. lib/
- `src/lib/utils.ts` — `cn()` (clsx + tailwind-merge), shadcn convention.
- `src/api/client.ts` (44 lines) — `apiFetch` with `credentials: include`, `X-Requested-With` CSRF header, single refresh-and-retry on 401, redirect to `/login` on failure.
- `GET /api/search?q=` accepts an empty query and returns suggestions; partial prefixes (e.g. `wire`) match novel/chapter titles accent-insensitively.

## 5. Patterns (SWR, state, forms)
- Plain React hooks (`useState`/`useEffect`) + `apiFetch`; no SWR/React Query in MVP.
- Forms are native `<form>` with controlled inputs (LoginForm); validation comes from backend 401/400 shown inline via `Alert`.
- Reading state: debounced (1s) `PUT /api/progress`; restore waits for text render (`requestAnimationFrame`) and suppresses scroll-save during restore.
- Chapter list uses `@tanstack/react-virtual` (rendered DOM bounded regardless of 1.700 chapters).
- Auth tokens never touch localStorage; `ThemeProvider` stores only the theme key.
