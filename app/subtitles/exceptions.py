from fastapi import HTTPException


class TrackNotFound(HTTPException):
    def __init__(self, video_id: int, language_code: str):
        super().__init__(status_code=404, detail=f"Subtitle track '{language_code}' not found for video {video_id}")


class InvalidSubtitleJSON(HTTPException):
    def __init__(self, reason: str):
        super().__init__(status_code=400, detail=f"Invalid subtitle JSON: {reason}")
