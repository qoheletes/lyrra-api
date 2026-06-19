# Session Progress Log

## Current State

**Last Updated:** 2026-06-18
**Active Feature:** auth-001 — Email/password identity (done, PR pending merge).

## Status (auth-001)

**Last Updated:** 2026-06-18
**Status:** `passing` — implemented, verified, Critic-approved; PR open for human merge.

### What's Done

- [x] **Option A — lean stateless access JWT.** New `src/auth/` package (sync SQLAlchemy,
      mirroring the `videos` area): `models.py` (`UserORM`, table `user`), `security.py`
      (bcrypt hash/verify, PyJWT HS256 issue/decode), `schemas.py`, `service.py`
      (`create_user`/`authenticate`/`get_user_by_id`), `exceptions.py`, `router.py`,
      `dependencies.py` (`get_current_user`).
- [x] Endpoints: `POST /auth/register` (201 → `UserOut`, **no token**, 409 on dup email),
      `POST /auth/login` (→ `{access_token, token_type: "bearer"}`, 401 on bad creds),
      `GET /auth/me` (Bearer → current user, 401 missing/invalid/expired).
- [x] `pyjwt` + `bcrypt` + `pydantic[email]` deps; JWT settings in `src/config.py`;
      `JWT_SECRET` default in `tests/conftest.py`.
- [x] Alembic migration `e704940455dc_create_user.py` (down_revision `82a4b8dc2f2d`).
- [x] Router + `UserORM` registered in `src/main.py`.
- [x] `tests/test_auth.py` (11 tests) — SQLite in-memory + `get_db` override so tests need no
      live Postgres (mirrors the `test_transcribe_e2e` no-lifespan pattern).
- [x] GitHub issue #10; implemented on branch `feature/email-password-auth`.

### Verification Evidence

- `./init.sh` → app boots (15 routes), `uv run pytest` → **25 passed**,
  `uv run ruff check src tests` → all checks passed.
- Route table lists `POST /auth/register`, `POST /auth/login`, `GET /auth/me`;
  tests assert `password_hash` is absent from every response body.

### Review fixes (Critic pass)

- **bcrypt 72-byte limit:** `password` `max_length` lowered 128 → 72 so an over-long password
  returns a clean **422** instead of bcrypt raising a 500; added a regression test.
- Cleared three ruff failures the implementation had been left with: TC002 (move `Session`
  into a `TYPE_CHECKING` block in `service.py`), RUF100 (drop unused `# noqa: F401` —
  `UserORM` is referenced), N806 (rename local `TestingSession` → `session_factory`).

### Notes / Risks

- `user` is a reserved word in Postgres (SQLAlchemy quotes it); the Alembic migration must be
  applied for real Postgres deploys — tests use SQLite + `create_all`, so they don't exercise it.
- `JWT_SECRET` in tests is short (triggers PyJWT's `InsecureKeyLengthWarning`); deployment must
  set a real ≥32-byte secret.
- `max_length=72` counts characters, not bytes; an all-multibyte 72-char password could still
  exceed 72 bytes. Acceptable edge for this lean slice; revisit if non-ASCII passwords matter.
- Sync DB layer deviates from `docs/auth-and-database.md`'s async target — accepted, matches
  existing code; async migration deferred project-wide.
- Out of scope (follow-ups): refresh tokens, logout/revocation, enforcing auth on existing routes.

---

## Status (youtube-001)

### What's Done

- [x] Renamed route `GET /youtube/transcribe/{video_id}/sentences` →
      `GET /youtube/{video_id}/transcript` in `src/youtube/router.py`.
- [x] Updated the two call sites in `tests/test_transcribe_e2e.py` (200 + 404 cases).
- [x] Response schema (`SentencesResponse`, `sentences` field) unchanged — path only.
- [x] GitHub issue #8; implemented on branch `feature/clarify-transcript-route`.

### Verification Evidence

- `uv run pytest` → 15 passed; `uv run ruff check src tests` → all checks passed.
- App route table lists `GET /youtube/{video_id}/transcript`; old path absent.
- No routing conflict with `/youtube/search` (single segment) or `/youtube/translate` (POST).

### Notes / Risks

- Scope was the URL path only. Handler name `get_sentences`, schema/field names,
  storage keys, and OpenAPI docs were intentionally left unchanged.
- Breaking change for any client calling the old path; no redirect/alias kept.

---

## Status (storage-003)

**Last Updated:** 2026-06-11
**Active Feature:** storage-003 — Per-video directory storage (done, PR pending merge)

## Status (storage-003)

### What's Done

- [x] `_sentences_key()` → `transcriptions/{video_id}/transcription.json`.
- [x] `_translation_key()` → `transcriptions/{video_id}/{lang}.json`
      (e.g. `transcriptions/{video_id}/es.json`).
- [x] Updated `tests/test_sentence_storage.py` expected keys for the new layout.
- [x] Updated `src/youtube/ARCHITECTURE.md` storage-key references (Transcription,
      new Translation entry, example dialogue).
- [x] GitHub issue #5; implemented on branch `feature/per-video-directory-storage`
      (cut from `feature/sentence-json-storage`).

### Verification Evidence

- `uv run pytest` → 10 passed; `uv run ruff check src tests` → all checks passed.

### Notes / Risks

- Payloads and gzip/Content-Encoding behavior are unchanged — only the object
  keys moved into a per-video directory.
- Public URL paths change; old flat objects (`transcriptions/{video_id}.json`,
  `*_translated_*.json`) are orphaned. No migration script.

## Status (storage-002)

### What's Done

- [x] `StorageAdapter.upload()` / `R2Adapter.upload()` accept optional
      `content_type` and `content_encoding`, forwarded to `put_object`.
- [x] `src/youtube/service.py`: removed `_save_transcription` and the raw
      `transcriptions/{video_id}.json` dump; the sentence payload
      (`video_id`, `title`, `duration_ms`, `source_url`, `language`,
      `sentences`) is now the only stored object, at
      `transcriptions/{video_id}.json`, serialized compactly and
      gzip-compressed (`Content-Encoding: gzip`, `Content-Type: application/json`).
- [x] `GetCachedTranscription` reads + gunzips the sentence file and derives
      the response (`text` joined from sentences, `words` flattened,
      `segments: []`, `transcription_url` from `get_public_url`).
- [x] `TranslateTranscription` reads the sentence payload and writes a
      gzip-compressed translation at `transcriptions/{video_id}_translated_{lang}.json`.
- [x] `GET /youtube/transcribe/{video_id}/sentences` returns stored sentences
      directly instead of rebuilding with `build_sentences`.
- [x] Added `tests/test_sentence_storage.py` (5 tests, fake storage adapter).
- [x] GitHub issue #3; implemented on branch `feature/sentence-json-storage`.

### Verification Evidence

- `uv run pytest` → 10 passed; `uv run ruff check src tests` → all checks passed

### Notes / Risks

- Speaker segments are no longer persisted; cached translate responses return
  `segments: []` (fresh transcriptions still include them in the API response).
- Existing bucket objects (`*_sentences.json`, old raw `{video_id}.json`) are
  orphaned — old raw files will fail to parse as sentence payloads only if a
  stale `{video_id}.json` raw dump exists for a video (it would lack
  `sentences`); re-transcribing overwrites it. No migration script written.

## Status (storage-001)

### What's Done

- [x] Removed `LocalFileAdapter` and `S3Adapter` from `src/storage/client.py`;
      `R2Adapter` now implements `StorageAdapter` directly with a top-level
      `boto3` import (boto3 is a declared dependency, so the lazy-import
      ImportError handling was dropped).
- [x] `get_storage()` always returns the R2 adapter and raises `StorageError`
      naming any missing `R2_*` env vars (lazy validation — app boots without
      R2 config, storage use fails loudly).
- [x] Removed `storage_backend`, `local_storage_path`, `local_storage_public_base`,
      `s3_bucket`, `s3_region` from `src/config.py`.
- [x] Removed the local `/files` StaticFiles mount from `src/main.py` plus its
      now-unused imports (`os`, `StaticFiles`, `settings`).
- [x] Added `tests/test_storage.py` (3 tests) and `tests/conftest.py` (env
      defaults so `src.config` imports without a real `.env`).
- [x] Created GitHub issue #1 and implemented on branch `feature/r2-only-storage`.

### Verification Evidence

- `./init.sh` → app boots (12 routes), 5 tests passed, ruff all checks passed
- grep for `LocalFileAdapter|S3Adapter|storage_backend|local_storage|StaticFiles|STORAGE_BACKEND|LOCAL_STORAGE`
  across `src/`, `tests/`, `scripts/`, `alembic/` → no matches

## Notes for Next Session

- Local `.env` may still contain `STORAGE_BACKEND`, `LOCAL_STORAGE_PATH`,
  `LOCAL_STORAGE_PUBLIC_BASE`, `S3_*` — now ignored; safe to delete manually.
- Existing files under any old local storage dir (e.g. `./data/subtitles`) were
  NOT migrated to R2; if any matter, upload them manually.
- Deferred (carried over): `pydantic-settings` BaseSettings config and async
  SQLAlchemy migration (see docs/), both out of scope here.
