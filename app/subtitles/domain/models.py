from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SubtitleTrack:
    id: int
    video_id: str
    language_code: str
    format: str
    file_url: str
    is_machine_translated: bool
    status: str
    created_at: datetime
    updated_at: datetime
    file_size_bytes: Optional[int] = None
