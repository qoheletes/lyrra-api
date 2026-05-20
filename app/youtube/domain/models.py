from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class WordTimestamp:
    word: str
    start: float
    end: float


@dataclass
class AudioDownloadResult:
    video_id: str
    title: str
    audio_path: str
    duration_ms: Optional[int] = None
    source_url: Optional[str] = None


@dataclass
class TranscriptionResult:
    language: str
    text: str
    words: List[WordTimestamp] = field(default_factory=list)
