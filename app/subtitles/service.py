from sqlalchemy.orm import Session

from app.storage.client import StorageAdapter
from app.subtitles.exceptions import InvalidSubtitleJSON, TrackNotFound
from app.subtitles.models import SubtitleTrack
from app.subtitles.validator import validate_subtitle_json
from app.videos.exceptions import VideoNotFound
from app.videos.models import Video


def upload_subtitle(
    video_id: int,
    language_code: str,
    fmt: str,
    file_bytes: bytes,
    db: Session,
    storage: StorageAdapter,
) -> SubtitleTrack:
    video = db.query(Video).filter(Video.id == video_id).first()
    if video is None:
        raise VideoNotFound(video_id)

    try:
        validate_subtitle_json(file_bytes)
    except ValueError as exc:
        raise InvalidSubtitleJSON(str(exc)) from exc

    key = f"{video_id}/{language_code}.{fmt}"
    file_url = storage.upload(key, file_bytes)

    track = (
        db.query(SubtitleTrack)
        .filter(SubtitleTrack.video_id == video_id, SubtitleTrack.language_code == language_code)
        .first()
    )
    if track is None:
        track = SubtitleTrack(video_id=video_id, language_code=language_code)
        db.add(track)

    track.format = fmt
    track.file_url = file_url
    track.file_size_bytes = len(file_bytes)
    db.commit()
    db.refresh(track)
    return track


def delete_subtitle(
    video_id: int,
    language_code: str,
    db: Session,
    storage: StorageAdapter,
) -> None:
    track = (
        db.query(SubtitleTrack)
        .filter(SubtitleTrack.video_id == video_id, SubtitleTrack.language_code == language_code)
        .first()
    )
    if track is None:
        raise TrackNotFound(video_id, language_code)

    key = f"{video_id}/{language_code}.{track.format}"
    storage.delete(key)
    db.delete(track)
    db.commit()
