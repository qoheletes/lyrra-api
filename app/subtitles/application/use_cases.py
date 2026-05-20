from __future__ import annotations

from app.core.storage.client import StorageAdapter
from app.subtitles.domain.exceptions import InvalidSubtitleJSONError, TrackNotFoundError
from app.subtitles.domain.models import SubtitleTrack
from app.subtitles.domain.validator import validate_subtitle_json
from app.subtitles.infrastructure.repository import SubtitleRepository
from app.videos.domain.exceptions import VideoNotFoundError
from app.videos.infrastructure.repository import VideoRepository


class UploadSubtitle:
    def __init__(
        self,
        subtitle_repo: SubtitleRepository,
        video_repo: VideoRepository,
        storage: StorageAdapter,
    ) -> None:
        self._subtitle_repo = subtitle_repo
        self._video_repo = video_repo
        self._storage = storage

    def execute(
        self,
        video_id: str,
        language_code: str,
        fmt: str,
        file_bytes: bytes,
    ) -> SubtitleTrack:
        if not self._video_repo.exists(video_id):
            raise VideoNotFoundError(video_id)
        try:
            validate_subtitle_json(file_bytes)
        except ValueError as exc:
            raise InvalidSubtitleJSONError(str(exc)) from exc
        key = f"{video_id}/{language_code}.{fmt}"
        file_url = self._storage.upload(key, file_bytes)
        return self._subtitle_repo.upsert(
            video_id=video_id,
            language_code=language_code,
            fmt=fmt,
            file_url=file_url,
            file_size_bytes=len(file_bytes),
        )


class DeleteSubtitle:
    def __init__(self, subtitle_repo: SubtitleRepository, storage: StorageAdapter) -> None:
        self._subtitle_repo = subtitle_repo
        self._storage = storage

    def execute(self, video_id: str, language_code: str) -> None:
        track = self._subtitle_repo.get_by_video_and_lang(video_id, language_code)
        key = f"{video_id}/{language_code}.{track.format}"
        self._storage.delete(key)
        self._subtitle_repo.delete(video_id, language_code)


class GetSubtitleTrackUrl:
    def __init__(self, subtitle_repo: SubtitleRepository) -> None:
        self._repo = subtitle_repo

    def execute(self, video_id: str, language_code: str) -> str:
        url = self._repo.find_file_url(video_id, language_code)
        if url is None:
            raise TrackNotFoundError(video_id, language_code)
        return url
