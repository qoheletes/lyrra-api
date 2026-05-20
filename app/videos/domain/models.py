from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class SubtitleTrackSummary:
    language_code: str
    file_url: str
    format: str


@dataclass
class Video:
    id: str
    title: str
    default_lang: str
    created_at: datetime
    updated_at: datetime
    duration_ms: Optional[int] = None
    source_url: Optional[str] = None
    translated_segments: Optional[list] = None
    translated_language: Optional[str] = None
    translated_text: Optional[str] = None
    subtitle_tracks: List[SubtitleTrackSummary] = field(default_factory=list)
