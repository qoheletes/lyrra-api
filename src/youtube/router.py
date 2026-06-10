from __future__ import annotations

import tempfile
from typing import Any
from urllib.parse import parse_qs, urlparse

from fastapi import APIRouter, BackgroundTasks, HTTPException

from src.config import settings
from src.storage.client import get_storage
from src.youtube.client import (
    OpenAITranslator,
    WhisperTranscriber,
    YouTubeAPISearcher,
    YtDlpAudioDownloader,
)
from src.youtube.exceptions import DownloadFailedError, TranscriptionFailedError
from src.youtube.schemas import (
    SentencesResponse,
    TranscriptionSegment,
    VideoSearchResultItem,
    WhisperWord,
    YouTubeSearchResponse,
    YouTubeTranslateRequest,
    YouTubeTranslateResponse,
)
from src.youtube.service import (
    GetCachedTranscription,
    SearchYouTubeVideos,
    TranslateTranscription,
    TranslateYouTubeVideo,
)

router = APIRouter(tags=["youtube"])


def _normalize_youtube_video_id(youtube_url: str) -> str | None:
    parsed = urlparse(youtube_url)
    host = parsed.netloc.lower()

    if host in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.lstrip("/").split("/")[0]
        return video_id or None

    if host.endswith("youtube.com"):
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        if parsed.path.startswith(("/shorts/", "/embed/", "/live/")):
            parts = [part for part in parsed.path.split("/") if part]
            if len(parts) >= 2:
                return parts[1]

    return None


def get_cached_transcription(video_id: str) -> dict[str, Any] | None:
    return GetCachedTranscription(get_storage()).execute(video_id)


def _run_background_translation(video_id: str, target_language: str) -> None:
    TranslateTranscription(get_storage(), OpenAITranslator()).execute(video_id, target_language)


def _build_translate_response(
    data: dict[str, Any], include_words: bool
) -> YouTubeTranslateResponse:
    words: list[WhisperWord] = []
    if include_words:
        words = [
            WhisperWord(word=w["word"], start=w["start"], end=w["end"])
            for w in data.get("words", [])
        ]
    segments = [
        TranscriptionSegment(speaker=s["speaker"], text=s["text"], start=s["start"], end=s["end"])
        for s in data.get("segments", [])
    ]
    return YouTubeTranslateResponse(
        title=data["title"],
        video_id=data["video_id"],
        source_language=data.get("language"),
        translated_text=data.get("text", ""),
        transcription_url=data.get("transcription_url"),
        words=words,
        segments=segments,
    )


@router.get("/youtube/search", response_model=YouTubeSearchResponse)
def search_youtube(
    q: str, max_results: int = 10, page_token: str | None = None
) -> YouTubeSearchResponse:
    searcher = YouTubeAPISearcher(settings.youtube_api_key)
    results = SearchYouTubeVideos(searcher).execute(q, max_results, page_token)
    return YouTubeSearchResponse(
        query=results.query,
        results=[
            VideoSearchResultItem(
                video_id=r.video_id,
                title=r.title,
                description=r.description,
                channel_title=r.channel_title,
                published_at=r.published_at,
                thumbnail_url=r.thumbnail_url,
                youtube_url=f"https://www.youtube.com/watch?v={r.video_id}",
            )
            for r in results.results
        ],
        next_page_token=results.next_page_token,
    )


@router.get("/youtube/transcribe/{video_id}/sentences", response_model=SentencesResponse)
def get_sentences(video_id: str) -> SentencesResponse:
    transcription = get_cached_transcription(video_id)
    if transcription is None:
        raise HTTPException(
            status_code=404, detail=f"No cached transcription for video_id={video_id!r}"
        )
    return SentencesResponse(
        video_id=video_id,
        language=transcription.get("language"),
        sentences=transcription["sentences"],
    )


@router.post("/youtube/translate", response_model=YouTubeTranslateResponse)
def translate_youtube_video(
    request: YouTubeTranslateRequest, background_tasks: BackgroundTasks
) -> YouTubeTranslateResponse:
    video_id = _normalize_youtube_video_id(str(request.youtube_url))
    storage = get_storage()
    if video_id:
        cached = get_cached_transcription(video_id)
        if cached:
            if request.target_language:
                background_tasks.add_task(
                    _run_background_translation, video_id, request.target_language
                )
            return _build_translate_response(cached, request.include_words)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            uc = TranslateYouTubeVideo(YtDlpAudioDownloader(), WhisperTranscriber(), storage)
            data = uc.execute(
                str(request.youtube_url),
                request.model,
                request.source_language,
                temp_dir,
            )
    except DownloadFailedError as exc:
        raise HTTPException(status_code=400, detail=f"YouTube download failed: {exc}") from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail="ffmpeg is required by yt-dlp/Whisper but was not found on the server.",
        ) from exc
    except TranscriptionFailedError as exc:
        raise HTTPException(status_code=500, detail=f"Whisper failed: {exc}") from exc

    if request.target_language:
        background_tasks.add_task(
            _run_background_translation, data["video_id"], request.target_language
        )

    return _build_translate_response(data, request.include_words)
