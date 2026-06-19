# Planning Meeting: auth-001 — Email/password identity (register, login, me)

- **Date:** 2026-06-18
- **Area:** auth
- **Status:** decided
- **Participants:** user, Claude

## Goal (user-visible behavior)

The API supports email/password identity backed by a JWT bearer token:

- `POST /auth/register` — create a user from `{email, password}`. Returns **201** with the
  created user (`id`, `email`, `created_at`) and **no token**. Duplicate email → 409.
- `POST /auth/login` — verify `{email, password}` and return `{access_token, token_type:
  "bearer"}` (a signed PyJWT HS256 token carrying the user id and an `exp`). Bad credentials → 401.
- `GET /auth/me` — given a valid `Authorization: Bearer <token>`, return the current user.
  Missing/invalid/expired token → 401.

**In scope:** the `user` table + migration, password hashing, JWT issue/verify, the three
endpoints, and a reusable `get_current_user` dependency.

**Explicitly out of scope:** enforcing auth on existing `youtube`/`videos`/`subtitles` routes
(they stay open — a deliberate follow-up feature); refresh tokens; logout/revocation;
password reset; email verification; roles/permissions; OAuth.

## Options considered

### Option A — Lean stateless access JWT  ✅ chosen
- How it works: new `src/auth/` package (`router.py`, `service.py`, `models.py`, `schemas.py`,
  `security.py`, `exceptions.py`) mirroring the `videos` area layout, using **sync** SQLAlchemy
  to match the existing codebase (`src/database.py` is sync `create_engine`/`Session`). One
  `user` table (`id`, `email` unique, `password_hash`, `created_at`, `updated_at`) via a new
  Alembic migration. `bcrypt` for hashing, `PyJWT` (HS256) issuing a single access token with
  `exp`. JWT settings (`JWT_SECRET`, `JWT_ALG`, access TTL) added to `src/config.py`.
- Pros: smallest correct slice; no extra tables; `get_current_user` is exactly what the
  route-enforcement follow-up reuses; fully stateless.
- Cons: no logout/revocation (token valid until expiry); no refresh (clients re-login on lapse).
- Effort / risk: **S–M / Low.**

### Option B — Access + refresh tokens  ❌ not chosen
- How it works: A plus a short-lived access JWT + longer-lived refresh JWT and `POST /auth/refresh`.
- Pros: better real-world UX; clients refresh without re-entering a password.
- Cons: more surface for a first slice; refresh tokens still stateless so revocation remains
  unsolved unless stored (that's C); extra TTLs + endpoint to test.
- Effort / risk: M / Low–Med.

### Option C — DB-backed sessions (revocable)  ❌ not chosen
- How it works: A plus an `auth_session`/refresh-token table (tokens stored hashed); login issues
  access JWT + stored refresh token; `POST /auth/logout` revokes; "log out everywhere" possible.
- Pros: real revocation and session management — the robust end state.
- Cons: most schema + endpoints; over-built for "identity only"; a table and lifecycle to test
  before any route is even protected.
- Effort / risk: M–L / Med.

## Decision

**Option A.** The user scoped this as "identity only," and A establishes every reusable
primitive — user model, bcrypt hashing, JWT plumbing, and the `get_current_user` dependency — at
the lowest risk. Refresh (B) and revocation (C) are natural follow-up features, the same way
route-enforcement already is; folding them in now would bloat the first slice. The user also
decided **`register` returns the created user (201), not a token** — clean separation, the client
calls `login` to obtain a token. Sync SQLAlchemy is used to match the existing area pattern
(`videos`/`subtitles`), even though `docs/auth-and-database.md` shows an async target; converting
the DB layer to async is out of scope here.

## Implementation plan

1. Add deps to `pyproject.toml`: `pyjwt` and `bcrypt` (run `uv sync`).
2. Extend `src/config.py` `Settings` with `jwt_secret` (required), `jwt_alg` (default `"HS256"`),
   and `access_token_ttl_min` (default e.g. 60). Add `JWT_SECRET` to `tests/conftest.py` env defaults.
3. `src/auth/models.py` — `UserORM` (`__tablename__ = "user"`): `id` (PK), `email`
   (`String`, unique, not null), `password_hash` (`String`, not null), `created_at`/`updated_at`
   (`server_default=func.now()`), following `VideoORM`'s column style and the index naming convention.
4. `src/auth/security.py` — `hash_password`/`verify_password` (bcrypt), `create_access_token(user_id)`
   and `decode_token(token)` (PyJWT, raising on invalid/expired).
5. `src/auth/schemas.py` — `RegisterRequest` / `LoginRequest` (`EmailStr`, password min-length via
   pydantic), `UserOut` (`id`, `email`, `created_at`), `TokenResponse` (`access_token`, `token_type`).
6. `src/auth/service.py` — `create_user` (hash + insert, raise on duplicate email),
   `authenticate` (lookup + verify), `get_user_by_id`.
7. `src/auth/exceptions.py` — `EmailAlreadyExists`, `InvalidCredentials`, `InvalidToken`.
8. `src/auth/router.py` — `APIRouter(prefix="/auth", tags=["auth"])` with
   `POST /register` (201 → `UserOut`, 409 on dup), `POST /login` (→ `TokenResponse`, 401),
   `GET /me` (→ `UserOut` via `get_current_user`). Map exceptions to `HTTPException`.
9. `get_current_user` dependency (in `src/auth/dependencies.py` or `router.py`): extract Bearer
   token (FastAPI `OAuth2PasswordBearer` or a header dep), decode, load user, 401 on failure.
10. Register the router in `src/main.py` (`app.include_router(auth_router)`).
11. New Alembic migration `alembic/versions/*_create_user.py` creating the `user` table
    (match the style of the existing `create_videos_and_subtitle_tracks` migration).
12. `tests/test_auth.py` — exercise register (201 + 409 dup), login (200 + 401 bad creds),
    `/me` (200 with token, 401 without/expired/invalid). Use httpx + ASGITransport per
    `docs/background-and-testing.md`.

## Verification plan

- `./init.sh` — `uv run pytest` + `uv run ruff check src tests` all pass.
- `tests/test_auth.py` proves: register returns 201 with the user and no token; duplicate email
  returns 409; login returns a bearer token; bad credentials return 401; `/me` returns the user
  for a valid token and 401 for missing/invalid/expired tokens.
- App route table lists `POST /auth/register`, `POST /auth/login`, `GET /auth/me`.
- `password_hash` is never present in any response body (bcrypt hash stays server-side).

## Open questions / risks

- **Migration runs against Postgres** — Alembic migration must be applied (or the test DB
  created) for `tests/test_auth.py`; confirm `init.sh`/test setup provisions the `user` table.
- `table name "user"` is a reserved word in Postgres; quoting is handled by SQLAlchemy but worth
  watching in raw SQL. Singular `user` matches the doc's naming convention.
- `JWT_SECRET` must be a real secret in deployment; tests use a fixed default via conftest.
- Sync-vs-async DB mismatch with `docs/auth-and-database.md` is a known, accepted deviation
  (matches existing code); a future async migration is deferred project-wide.
