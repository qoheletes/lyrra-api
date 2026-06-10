# Session Progress Log

## Current State

**Last Updated:** 2026-06-10
**Active Feature:** storage-001 — Store only to R2 (done, PR pending merge)

## Status

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
