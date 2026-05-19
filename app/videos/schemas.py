from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class SubtitleTrackOut(BaseModel):
    language_code: str
    file_url: str
    format: str

    model_config = {"from_attributes": True}


class VideoOut(BaseModel):
    id: int
    title: str
    duration_ms: Optional[int]
    source_url: Optional[str]
    default_lang: str
    created_at: datetime
    updated_at: datetime
    subtitle_tracks: List[SubtitleTrackOut]

    model_config = {"from_attributes": True}
