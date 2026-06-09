from datetime import datetime

from pydantic import BaseModel


class SubtitleTrackOut(BaseModel):
    id: int
    video_id: str
    language_code: str
    format: str
    file_url: str
    file_size_bytes: int | None
    is_machine_translated: bool
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
