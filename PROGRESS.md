# Session Progress Log

## Current State

**Last Updated:** 2026-06-10
**Active Feature:** storage-002 — Store only compressed sentence JSON (done, PR pending merge)

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
