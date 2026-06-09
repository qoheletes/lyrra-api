from pydantic import BaseModel, Field, HttpUrl


class SentenceWord(BaseModel):
    word: str
    start: float
    end: float


class Sentence(BaseModel):
    text: str
    start: float
    end: float
    words: list[SentenceWord]


class YouTubeSearchRequest(BaseModel):
    q: str = Field(description="Search query")
    max_results: int = Field(default=10, ge=1, le=50, description="Number of results to return")
    page_token: str | None = Field(
        default=None, description="Pagination token from a previous search"
    )


class VideoSearchResultItem(BaseModel):
    video_id: str
    title: str
    description: str
    channel_title: str
    published_at: str
    thumbnail_url: str | None = None
    youtube_url: str


class YouTubeSearchResponse(BaseModel):
    query: str
    results: list[VideoSearchResultItem]
    next_page_token: str | None = None


class YouTubeTranslateRequest(BaseModel):
    youtube_url: HttpUrl
    model: str = Field(default="whisper-1", description="OpenAI transcription model name")
    source_language: str | None = Field(
        default=None,
        description="Optional source language code like 'ko' or 'ja'",
    )
    include_words: bool = Field(
        default=True,
        description="Include word-level timestamps in the response",
    )
    target_language: str | None = Field(
        default=None,
        description="Target language for async background translation (e.g. 'es', 'ko', 'ja'). "
        "Translation runs after the response is returned.",
    )


class WhisperWord(BaseModel):
    word: str
    start: float
    end: float


class TranscriptionSegment(BaseModel):
    speaker: str
    text: str
    start: float
    end: float


class YouTubeTranslateResponse(BaseModel):
    title: str
    video_id: str
    source_language: str | None
    translated_text: str
    transcription_url: str | None = None
    words: list[WhisperWord] = Field(default_factory=list)
    segments: list[TranscriptionSegment] = Field(default_factory=list)


class SentencesResponse(BaseModel):
    video_id: str
    language: str | None
    sentences: list[Sentence]
