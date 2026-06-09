# Subtitles

Manages subtitle files for videos: upload (with JSON validation), delete, and redirect to the file URL for a given video+language pair.

## Module layout

Flat, domain-scoped modules (see `docs/project-structure.md`):

- `models.py` — `SubtitleTrackORM` SQLAlchemy model (table `subtitle_tracks`)
- `schemas.py` — `SubtitleTrackOut` Pydantic response model
- `service.py` — `upload_subtitle`, `delete_subtitle`, `get_track_url` functions
- `utils.py` — `validate_subtitle_json`
- `router.py` — FastAPI router under `/videos/{video_id}/subtitles`
- `exceptions.py` — `InvalidSubtitleJSONError`, `TrackNotFoundError`

## Data Flow

### Upload
1. Router receives `POST /videos/{video_id}/subtitles` with file bytes, `language_code`, `format`
2. `service.upload_subtitle` calls `videos.service.exists` — raises `VideoNotFoundError` if the video is unknown
3. File bytes are validated with `validate_subtitle_json` — raises `InvalidSubtitleJSONError` on bad content
4. File is uploaded to the `StorageAdapter` at key `{video_id}/{language_code}.{format}` → returns `file_url`
5. The `subtitle_tracks` row is upserted (insert or update on `(video_id, language_code)`)
6. Router returns `SubtitleTrackOut.model_validate(track)`

### Delete
1. Router receives `DELETE /videos/{video_id}/subtitles/{language_code}`
2. `service.delete_subtitle` loads the track to resolve the storage key, deletes the file from the `StorageAdapter`, then deletes the DB row

### Get URL
1. Router receives `GET /videos/{video_id}/subtitles/{language_code}`
2. `service.get_track_url` looks up `file_url` from the DB
3. Router issues a `302 redirect` to the file URL

## Glossary

**SubtitleTrack** — The full entity for a subtitle file. Fields: `id`, `video_id`, `language_code`, `format`, `file_url`, `is_machine_translated`, `status`, `created_at`, `updated_at`, `file_size_bytes`. Stored in the `subtitle_tracks` Postgres table as `SubtitleTrackORM`. One row per `(video_id, language_code)` pair (upsert semantics).

**SubtitleJSON** — The expected shape of an uploaded subtitle file. Must be valid JSON. Validated by `validate_subtitle_json` before any storage write occurs.

**SubtitleKey** — The object storage key for a subtitle file: `{video_id}/{language_code}.{format}`. Derived deterministically from the track's identifiers. There is no separate "key" field — the key is always re-derived when needed.

**TrackNotFoundError** — Raised when a `(video_id, language_code)` pair has no row in `subtitle_tracks`. Signals a 404.

**InvalidSubtitleJSONError** — Raised when uploaded bytes fail `validate_subtitle_json`. Signals a 400.

## Example dialogue

> **Dev**: If I upload a subtitle for the same language twice, do I get two rows?
>
> **Domain expert**: No — `upload_subtitle` upserts on `(video_id, language_code)`. The second upload replaces the first row and overwrites the file in storage at the same key.
>
> **Dev**: What is `is_machine_translated` set to on upload?
>
> **Domain expert**: The upload endpoint doesn't accept that field from the caller today. New rows take the column default (`False`); it's not surfaced in the request schema.
