class TrackNotFoundError(Exception):
    def __init__(self, video_id: str, language_code: str) -> None:
        super().__init__(f"Subtitle track '{language_code}' not found for video {video_id}")
        self.video_id = video_id
        self.language_code = language_code


class InvalidSubtitleJSONError(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(f"Invalid subtitle JSON: {reason}")
        self.reason = reason
