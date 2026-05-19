from fastapi import HTTPException


class VideoNotFound(HTTPException):
    def __init__(self, video_id: int):
        super().__init__(status_code=404, detail=f"Video {video_id} not found")
