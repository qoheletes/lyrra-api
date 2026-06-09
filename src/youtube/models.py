from __future__ import annotations

from dataclasses import dataclass, field


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
    duration_ms: int | None = None
    source_url: str | None = None


@dataclass
class SpeakerSegment:
    speaker: str
    text: str
    start: float
    end: float


@dataclass
class TranscriptionResult:
    language: str
    text: str
    words: list[WordTimestamp] = field(default_factory=list)
    segments: list[SpeakerSegment] = field(default_factory=list)


@dataclass
class VideoSearchResult:
    video_id: str
    title: str
    description: str
    channel_title: str
    published_at: str
    thumbnail_url: str | None = None


@dataclass
class VideoSearchResults:
    query: str
    results: list[VideoSearchResult] = field(default_factory=list)
    next_page_token: str | None = None
