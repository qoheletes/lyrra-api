from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl

from app.youtube.domain.sentences import Sentence, SentenceWord  # noqa: F401 — re-exported


class YouTubeTranslateRequest(BaseModel):
    youtube_url: HttpUrl
    model: str = Field(default="whisper-1", description="Whisper model name")
    source_language: Optional[str] = Field(
        default=None,
        description="Optional source language code like 'ko' or 'ja'",
    )
    include_words: bool = Field(
        default=True,
        description="Include word-level timestamps in the response",
    )


class WhisperWord(BaseModel):
    word: str
    start: float
    end: float


class YouTubeTranslateResponse(BaseModel):
    title: str
    video_id: str
    source_language: Optional[str]
    translated_text: str
    words: List[WhisperWord] = Field(default_factory=list)


class SentencesResponse(BaseModel):
    video_id: str
    language: Optional[str]
    sentences: List[Sentence]
