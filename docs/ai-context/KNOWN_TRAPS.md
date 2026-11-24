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

## 14. Launcher must supervise children, not just wait for them
`start.py` had `deadline = time.time() + 180` (smoke-test guard) — removed, but two more failure modes remained: (a) the loop exited as soon as **one** child died, killing the session; (b) `SetConsoleCtrlHandler` called `taskkill` from the OS-created callback thread, which could leave the frontend orphaned. Worse, Windows terminates a process on Ctrl+C/Break/close with `0xC000013A` **before** Python's `finally` runs unless the console handler swallows the event. Current design: console handler only sets a `CLOSE_EVENT` (never spawns processes), main loop restarts an unexpectedly dead child (max 5), startup logs go to `logs/*.log`, no `--reload` from the launcher, and `start.bat` always `pause`s. Keep test-only timeouts in tests, not in shipped entry points.


## 15. Manga scan needs a wider fingerprint column and a root prefix
`ScanLog.fingerprint` was `VARCHAR(64)`; prefixing the manga fingerprint with `manga:` makes it 70 chars → Postgres rejects the insert, so manga chapters never appear. Fix: Alembic 0005 widens the column to 80; keep the prefix to separate text/manga skip decisions. Prefix `Novel.source_dir` with `manhwa:` because a title can exist in both roots. Do **not** mutate `Novel.title` (an earlier ` (manga)` suffix was ugly and forced path hacks — Alembic 0006 removes it); expose `NovelOut.kind` instead and let the card render a `Novel`/`Manhwa` badge.

## 16. Continuous manga scroll needs reserved image layout and a restore gate
`loading="lazy"` images with no `width`/`height` collapse to zero height before load, so `scrollIntoView()` to the saved page lands at the top and the IntersectionObserver only ever sees page 1. Fix: give every `<img>` explicit `width`/`height` (aspect-ratio hint) and suppress observer-driven progress until the restore `requestAnimationFrame` has completed — otherwise page 1 overwrites the saved page before scrolling finishes.

## 17. Virtualenv stub owns the Windows Terminal tab
`backend/.venv/Scripts/python.exe` is a virtualenv **stub** that re-execs the real interpreter as a child (two python.exe processes with the same command line — not a double launch). When the launcher spawns it with `CREATE_NEW_CONSOLE`, the stub is the root of that Windows Terminal tab: if its uvicorn child exits, the stub exits and the **whole tab disappears**, even though the launcher is still alive. Never infer "the user closed the terminal" from a vanished child tab; supervise/restart the child instead. Ctrl events from uvicorn's Windows `--reload` (`os.kill(pid, CTRL_C_EVENT)`) make this worse — the launcher starts uvicorn without `--reload`.
