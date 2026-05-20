from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.subtitles.domain.exceptions import TrackNotFoundError
from app.subtitles.domain.models import SubtitleTrack
from app.subtitles.infrastructure.orm_models import SubtitleTrackORM


class SubtitleRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def find_by_video_and_lang(self, video_id: str, language_code: str) -> Optional[SubtitleTrack]:
        row = (
            self._db.query(SubtitleTrackORM)
            .filter(
                SubtitleTrackORM.video_id == video_id,
                SubtitleTrackORM.language_code == language_code,
            )
            .first()
        )
        return self._to_domain(row) if row else None

    def get_by_video_and_lang(self, video_id: str, language_code: str) -> SubtitleTrack:
        track = self.find_by_video_and_lang(video_id, language_code)
        if track is None:
            raise TrackNotFoundError(video_id, language_code)
        return track

    def upsert(
        self,
        video_id: str,
        language_code: str,
        fmt: str,
        file_url: str,
        file_size_bytes: int,
    ) -> SubtitleTrack:
        row = (
            self._db.query(SubtitleTrackORM)
            .filter(
                SubtitleTrackORM.video_id == video_id,
                SubtitleTrackORM.language_code == language_code,
            )
            .first()
        )
        if row is None:
            row = SubtitleTrackORM(video_id=video_id, language_code=language_code)
            self._db.add(row)
        row.format = fmt
        row.file_url = file_url
        row.file_size_bytes = file_size_bytes
        self._db.commit()
        self._db.refresh(row)
        return self._to_domain(row)

    def delete(self, video_id: str, language_code: str) -> None:
        row = (
            self._db.query(SubtitleTrackORM)
            .filter(
                SubtitleTrackORM.video_id == video_id,
                SubtitleTrackORM.language_code == language_code,
            )
            .first()
        )
        if row is None:
            raise TrackNotFoundError(video_id, language_code)
        self._db.delete(row)
        self._db.commit()

    def find_file_url(self, video_id: str, language_code: str) -> Optional[str]:
        return (
            self._db.query(SubtitleTrackORM.file_url)
            .filter(
                SubtitleTrackORM.video_id == video_id,
                SubtitleTrackORM.language_code == language_code,
            )
            .scalar()
        )

    @staticmethod
    def _to_domain(row: SubtitleTrackORM) -> SubtitleTrack:
        return SubtitleTrack(
            id=row.id,
            video_id=row.video_id,
            language_code=row.language_code,
            format=row.format,
            file_url=row.file_url,
            file_size_bytes=row.file_size_bytes,
            is_machine_translated=row.is_machine_translated,
            status=row.status,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
