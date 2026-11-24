# KNOWN_TRAPS — inkwell

> Pitfalls already hit — record them so they never repeat. Format: ## N. trap name + explanation + fix.

## 1. `__dirname` is undefined in ESM Playwright config
`playwright.config.ts` runs as ESM (`"type": "module"`); `__dirname` throws `ReferenceError`. Fix: `const root = fileURLToPath(new URL('.', import.meta.url))`.

## 2. jsdom lacks ResizeObserver and scrollIntoView
Radix ScrollArea/Slider/Command and cmdk call `ResizeObserver` and `element.scrollIntoView`, which don't exist in jsdom — component tests crash. Fix: stub both in `src/test-setup.ts` (also mock `offsetHeight`/`offsetWidth` for virtualizer layout).

## 3. shadcn ThemeProvider localStorage is fine, token storage is not
The shadcn dark-mode guide stores the theme in localStorage. That is safe; storing JWT/tokens there is not (project rule: HttpOnly cookies only). Keep `ThemeProvider` theme-only.

## 4. Numeric chapter filter must be exact
Substring filtering turns "128" into 1128/1280/… Fix: if the query is all digits, match `String(chapter.number) === query` exactly (`filterChapters` in `virtual-chapter-list.tsx`).

## 5. Playwright locators on cmdk input
cmdk renders its input with `role="combobox"`, not `textbox`; `getByPlaceholder` with Vietnamese diacritics was brittle in this shell. Fix: `page.getByRole('combobox', { name: 'Tìm kiếm' })`.

## 6. Fixed floating action overlaps the chapter navigation
A `fixed bottom-4 right-4` chapter-list trigger sat on top of the "Chương sau" button at the article bottom. Fix: remove the floating trigger; the controlled `Sheet` is opened from the ReaderToolbar button instead, and prev/next stay in one normal flow row. Verified with a full-page screenshot.

## 7. Dialog animation keyframes must not set `transform`
A `dialog-in` keyframe that ended with `translate(-50%, -50%)` overrode the Tailwind translate utilities that position `DialogContent`, pushing the command palette off-centre and clipping its input. Fix: animate `opacity` + the independent `scale` property only; leave positioning `transform` to the classes.

## 8. cmdk `CommandEmpty` renders before any search happens
With an empty hit list, cmdk shows `CommandEmpty` immediately — the palette displayed "Không tìm thấy kết quả" while the input was still empty. Fix: gate it on `query.trim() && !loading && hits.length === 0`, and fetch suggestions for the empty query.

## 9. Postgres FTS alone can't do prefix search
`websearch_to_tsquery('simple', unaccent(q))` matches whole lexemes only, so "wire" missed "Wireless_Onahole". Fix: OR it with `unaccent(c.title) ILIKE '%' || unaccent(:q) || '%'` (and novel title), ordering exact prefixes first.

## 10. `[role="combobox"]:focus-visible` specificity beats `input:focus-visible`
cmdk's input carries `role="combobox"`, so the generic combobox outline rule (specificity 0,2,0) overrode the input no-outline rule (0,1,1), drawing a 2px amber rectangle + 2px offset outside the searchbar. Fix: drop combobox from the outline list and add an explicit `input[role="combobox"]:focus-visible` rule (0,2,1) with `outline: none`; show focus via the wrapper's `focus-within:border-accent` instead.

## 11. `asChild` children must forward refs (Button!)
The account dropdown appeared to open but its content sat at `translate(0, -200%)` off-screen. Root cause: our `Button` was a plain function component, so Radix `Slot` (via `DropdownMenuTrigger asChild`) could not attach a ref to the DOM button → Popper had no anchor and never positioned the menu. Fix: `React.forwardRef<HTMLButtonElement, ButtonProps>` on `Button`. Secondary: don't wrap a `DropdownMenu` root in `TooltipTrigger asChild` — keep Tooltip inside the menu with the trigger button as the `asChild` child. Verify with a real browser: `toBeVisible()` passes for off-screen portals; assert the menu's bounding box `y > 0`.

## 12. `getByLabel` substring collisions and zero-height virtualizers
Adding `aria-label="Hiện mật khẩu"` made `getByLabel('Mật khẩu')` match both the input and the toggle in E2E — use `getByLabel('Mật khẩu', { exact: true })`. Also, `useVirtualizer` reports zero rows in jsdom/hidden panels; render a bounded first-page fallback (≤12 rows) so rows are never blank while keeping DOM bounded.

## 13. Docker needs host-reachable DB URLs and time on Windows bind mounts
`localhost` in `.env` points at the container, not the host → backend startup hung on DB connection. Fix: gitignored `.env.docker` rewriting DB URLs to `host.docker.internal` (compose loads it after `.env`). Also the first scan over a `drafts/Novel/` bind mount on Docker Desktop took ~90 s — let startup finish before smoke-testing. PowerShell `curl --data-raw $json` mangles JSON; write the body to a file and use `--data-binary @file`.

## 14. Smoke-test deadline leaked into a user-facing launcher
`start.py` had `deadline = time.time() + 180` (a guard for background smoke tests). Shipped as-is, the launcher silently exited after 3 min and its `finally` killed both dev servers — the owner saw consoles close for no reason. Fix: user-facing launchers wait until the user closes them / Ctrl+C, and only exit early on a real child failure, with a visible error + pause. Keep test-only timeouts in tests, not in shipped entry points.

## 15.
