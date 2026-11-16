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

## 6.
