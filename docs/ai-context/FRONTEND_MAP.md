# FRONTEND_MAP — inkwell

## 1. Routes
| Route | File | Lines | Notes |
|---|---|---:|---|
| `/login` | `novel_reader/frontend/src/pages/Login.tsx` | 8 | Composes `LoginForm`; dark branded card |
| `/` | `novel_reader/frontend/src/pages/Library.tsx` | 116 | Library grid (titles only), EN/VI tabs, virtualized chapter list, ⌘K |
| `/read/:chapterId` | `novel_reader/frontend/src/pages/Reader.tsx` | 152 | Reader with font controls, progress, shortcuts, mobile sheet |

## 2. Key components
- `components/ui/` — 483 lines, 24 files: shadcn/new-york primitives (Radix-based). One primary component per file: button, input, label, card, badge, separator, skeleton, alert, spinner, empty, kbd, typography, tooltip, progress, tabs, dropdown-menu, scroll-area, slider, dialog, sheet, command, sonner, switch, toggle-group. Compound parts (CardHeader, TabsTrigger, …) live with their family.
- `components/app/` — 536 lines, 15 files, one responsibility per file: theme-provider, app-header, login-form, novel-card, variants-tabs, search-command, chapter-filter, virtual-chapter-list, reader-toolbar, reader-view, reading-progress, mobile-chapter-sheet, keyboard-shortcuts, empty-state, error-state.

## 3. UI conventions
- Single dark theme "Night reading desk": warm graphite `#15130f`, parchment-tinted card `#1e1b16`, one amber accent `#e0a458`; tokens in `src/index.css` (`@theme inline`).
- Tailwind CSS v4 via `@tailwindcss/vite`; shadcn style `new-york` (`components.json`); lucide icons; serif (Newsreader) for chapter text, mono numerals for chapter numbers.
- No covers/images in library — titles only (owner requirement).
- Every async path has loading skeletons, empty state, or error alert; toasts for saved position.
- Keyboard: ⌘K search; J/K or ←/→ chapter nav; Esc closes overlays. Mobile: chapter list in a `Sheet`.

## 4. lib/
- `src/lib/utils.ts` — `cn()` (clsx + tailwind-merge), shadcn convention.
- `src/api/client.ts` (44 lines) — `apiFetch` with `credentials: include`, `X-Requested-With` CSRF header, single refresh-and-retry on 401, redirect to `/login` on failure.

## 5. Patterns (SWR, state, forms)
- Plain React hooks (`useState`/`useEffect`) + `apiFetch`; no SWR/React Query in MVP.
- Forms are native `<form>` with controlled inputs (LoginForm); validation comes from backend 401/400 shown inline via `Alert`.
- Reading state: debounced (1s) `PUT /api/progress`; restore waits for text render (`requestAnimationFrame`) and suppresses scroll-save during restore.
- Chapter list uses `@tanstack/react-virtual` (rendered DOM bounded regardless of 1.700 chapters).
- Auth tokens never touch localStorage; `ThemeProvider` stores only the theme key.
