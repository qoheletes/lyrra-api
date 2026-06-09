# Videos

Stores video records and exposes them with their attached subtitle track metadata.

## Module layout

The domain is organized as flat, domain-scoped modules (see `docs/project-structure.md`):

- `models.py` — `VideoORM` SQLAlchemy model (table `videos`)
- `schemas.py` — `VideoOut`, `SubtitleTrackOut` Pydantic response models
- `service.py` — `get_with_tracks`, `exists` data-access functions
- `router.py` — FastAPI router for `GET /videos/{video_id}`
- `exceptions.py` — `VideoNotFoundError`

## Data Flow

1. Router receives `GET /videos/{video_id}`
2. `service.get_with_tracks(db, video_id)` queries `VideoORM` with `selectinload(subtitle_tracks)`, raising `VideoNotFoundError` if missing
3. Router hydrates the ORM row directly into `VideoOut` via `VideoOut.model_validate(video)` — the response schema reads the eager-loaded relationship by attribute (`from_attributes=True`)

There is no intermediate domain dataclass: SQL produces the ORM row, Pydantic validates it for the response.

## Glossary

**Video** — The core entity. Identified by `id` (a YouTube VideoId string). Carries `title`, `default_lang`, timestamps, optional `duration_ms` and `source_url`. Stored in the `videos` Postgres table as `VideoORM`.

**VideoOut** — The Pydantic response shape. Includes a `subtitle_tracks` list of `SubtitleTrackOut`, a lightweight projection (`language_code`, `file_url`, `format`) validated straight off the `VideoORM.subtitle_tracks` relationship. This is intentionally smaller than the Subtitles domain's `SubtitleTrackOut`, which carries the full track (status, `is_machine_translated`, `file_size_bytes`, etc.).

**videos.service** — The persistence boundary for this domain. Exposes `get_with_tracks`, `exists`. Does not create or mutate Videos — creation happens out-of-band (e.g., migration or a future endpoint).

## Flagged ambiguities

- **`VideoORM.translated_*` fields**: The model carries `translated_segments`, `translated_language`, and `translated_text` as optional columns. No current endpoint populates them — they appear to be leftovers from a pre-refactor design where translation results were stored in the DB. Treat them as dead weight until something explicitly writes them.

## Example dialogue

> **Dev**: How does a Video get created?
>
> **Domain expert**: There's no create endpoint right now. Videos come into existence through migration scripts or direct DB inserts. The API only reads them.
>
> **Dev**: So `GET /videos/{id}` will 404 on any video that was never manually inserted?
>
> **Domain expert**: Correct. And subtitle upload will also 404 before it creates a track, because it checks `videos.service.exists` first.
