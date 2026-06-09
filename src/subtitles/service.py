from __future__ import annotations

from typing import TYPE_CHECKING

from src.subtitles.exceptions import InvalidSubtitleJSONError, TrackNotFoundError
from src.subtitles.models import SubtitleTrackORM
from src.subtitles.utils import validate_subtitle_json
from src.videos import service as videos_service
from src.videos.exceptions import VideoNotFoundError

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from src.storage.client import StorageAdapter


def _find_track(db: Session, video_id: str, language_code: str) -> SubtitleTrackORM | None:
    return (
        db.query(SubtitleTrackORM)
        .filter(
            SubtitleTrackORM.video_id == video_id,
            SubtitleTrackORM.language_code == language_code,
        )
        .first()
    )


def upload_subtitle(
    db: Session,
    storage: StorageAdapter,
    video_id: str,
    language_code: str,
    fmt: str,
    file_bytes: bytes,
) -> SubtitleTrackORM:
    if not videos_service.exists(db, video_id):
        raise VideoNotFoundError(video_id)
    try:
        validate_subtitle_json(file_bytes)
    except ValueError as exc:
        raise InvalidSubtitleJSONError(str(exc)) from exc

    key = f"{video_id}/{language_code}.{fmt}"
    file_url = storage.upload(key, file_bytes)

    row = _find_track(db, video_id, language_code)
    if row is None:
        row = SubtitleTrackORM(video_id=video_id, language_code=language_code)
        db.add(row)
    row.format = fmt
    row.file_url = file_url
    row.file_size_bytes = len(file_bytes)
    db.commit()
    db.refresh(row)
    return row


def delete_subtitle(
    db: Session,
    storage: StorageAdapter,
    video_id: str,
    language_code: str,
) -> None:
    row = _find_track(db, video_id, language_code)
    if row is None:
        raise TrackNotFoundError(video_id, language_code)
    storage.delete(f"{video_id}/{language_code}.{row.format}")
    db.delete(row)
    db.commit()


def get_track_url(db: Session, video_id: str, language_code: str) -> str:
    url = (
        db.query(SubtitleTrackORM.file_url)
        .filter(
            SubtitleTrackORM.video_id == video_id,
            SubtitleTrackORM.language_code == language_code,
        )
        .scalar()
    )
    if url is None:
        raise TrackNotFoundError(video_id, language_code)
    return url
