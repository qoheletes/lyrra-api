from __future__ import annotations

from sqlalchemy.orm import Session, selectinload

from src.videos.exceptions import VideoNotFoundError
from src.videos.models import VideoORM


def get_with_tracks(db: Session, video_id: str) -> VideoORM:
    row = (
        db.query(VideoORM)
        .options(selectinload(VideoORM.subtitle_tracks))
        .filter(VideoORM.id == video_id)
        .first()
    )
    if row is None:
        raise VideoNotFoundError(video_id)
    return row


def exists(db: Session, video_id: str) -> bool:
    return db.query(VideoORM.id).filter(VideoORM.id == video_id).scalar() is not None
