# Session Progress Log

## Current State

**Last Updated:** 2026-06-17
**Active Feature:** youtube-001 — Rename sentences route to GET /youtube/{video_id}/transcript (done, PR pending)

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
