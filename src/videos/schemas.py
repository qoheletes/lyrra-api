from datetime import datetime

from pydantic import BaseModel


class SubtitleTrackOut(BaseModel):
    language_code: str
    file_url: str
    format: str

    model_config = {"from_attributes": True}


class VideoOut(BaseModel):
    id: str
    title: str
    duration_ms: int | None
    source_url: str | None
    default_lang: str
    created_at: datetime
    updated_at: datetime
    subtitle_tracks: list[SubtitleTrackOut]

    model_config = {"from_attributes": True}
