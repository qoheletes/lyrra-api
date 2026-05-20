from __future__ import annotations

from sqlalchemy.orm import Session, selectinload

from app.videos.domain.exceptions import VideoNotFoundError
from app.videos.domain.models import SubtitleTrackSummary, Video
from app.videos.infrastructure.orm_models import VideoORM


class VideoRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_with_tracks(self, video_id: str) -> Video:
        row = (
            self._db.query(VideoORM)
            .options(selectinload(VideoORM.subtitle_tracks))
            .filter(VideoORM.id == video_id)
            .first()
        )
        if row is None:
            raise VideoNotFoundError(video_id)
        return self._to_domain(row)

    def exists(self, video_id: str) -> bool:
        return (
            self._db.query(VideoORM.id).filter(VideoORM.id == video_id).scalar()
            is not None
        )

    @staticmethod
    def _to_domain(row: VideoORM) -> Video:
        return Video(
            id=row.id,
            title=row.title,
            default_lang=row.default_lang,
            created_at=row.created_at,
            updated_at=row.updated_at,
            duration_ms=row.duration_ms,
            source_url=row.source_url,
            translated_segments=row.translated_segments,
            translated_language=row.translated_language,
            translated_text=row.translated_text,
            subtitle_tracks=[
                SubtitleTrackSummary(
                    language_code=t.language_code,
                    file_url=t.file_url,
                    format=t.format,
                )
                for t in row.subtitle_tracks
            ],
        )
