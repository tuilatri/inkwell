# API_MAP — inkwell

> Map of every endpoint: method, path, auth, rate limit, response shape.
> Backend: `novel_reader/backend/app/api/` · prefix `/api` · all routes require the `nr_access` HttpOnly cookie.

## Endpoints

| Method | Path | Auth | Rate limit | Description |
|---|---|---|---|---|
| POST | `/api/auth/login` | No | 5 failures / 60 s per username+host (in-memory) | Seed/verify admin, set access+refresh cookies |
| POST | `/api/auth/refresh` | Refresh cookie + CSRF | — | Rotate refresh token, issue new access token |
| POST | `/api/auth/logout` | Access cookie + CSRF | — | Revoke jti rows, clear cookies |
| POST | `/api/auth/change-password` | Access cookie + CSRF | — | Rehash password, revoke all sessions (env seed becomes void) |
| GET | `/api/auth/me` | Access cookie | — | Current admin `{id, username}` |
| GET | `/api/novels` | Access cookie | — | `[{id, title}]` — names only, no covers |
| GET | `/api/novels/{id}/variants` | Access cookie | — | `[{id, lang}]` — `vi` / `en` |
| GET | `/api/variants/{id}/chapters` | Access cookie | — | `[{id, number, title, visited}]` — active chapters, ordered; names only (no content), `visited` = `reading_state.scroll_pos > 0` |
| GET | `/api/chapters/{id}` | Access cookie | — | Chapter metadata; 404 if soft-deleted |
| GET | `/api/chapters/{id}/content` | Access cookie | — | `text/plain; charset=utf-8` streamed from `drafts/Novel/` |
| PUT | `/api/progress` | Access cookie + CSRF | — | `{chapter_id, scroll_pos}` → upsert reading state |
| GET | `/api/progress/{chapter_id}` | Access cookie | — | `{chapter_id, scroll_pos}` (0 if absent) |
| GET | `/api/search?q=&variant_id=` | Access cookie | — | `SearchHit[]`; empty `q` = suggestions; accent-insensitive prefix |
| POST | `/api/admin/rescan` | Access cookie + CSRF | — | Rescan `drafts/Novel/` + rebuild FTS index |

## Conventions
- Rate limit storage: in-memory dict `_FAILED` in `api/auth.py` (login only, resets on restart — no Redis in MVP).
- Auth scheme: argon2id hash; JWT HS256 in `nr_access` (20 min) + `nr_refresh` (14 d) HttpOnly/SameSite=Strict cookies; `jti` in `token_sessions` for revocation; no token in localStorage.
- CSRF: `X-Requested-With: XMLHttpRequest` required on every POST/PUT/DELETE (except `/auth/login`).
- Every `/api/*` response carries `Cache-Control: no-store, private` + CSP / X-Frame-Options / Referrer-Policy headers.
- Errors use FastAPI HTTPException `{detail}`; frontend shows `Alert`/toast in Vietnamese.
