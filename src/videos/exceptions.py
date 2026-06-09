class VideoNotFoundError(Exception):
    def __init__(self, video_id: str) -> None:
        super().__init__(f"Video {video_id!r} not found")
        self.video_id = video_id
