from app.videos.domain.models import Video
from app.videos.infrastructure.repository import VideoRepository


class GetVideoWithTracks:
    def __init__(self, repo: VideoRepository) -> None:
        self._repo = repo

    def execute(self, video_id: str) -> Video:
        return self._repo.get_with_tracks(video_id)
