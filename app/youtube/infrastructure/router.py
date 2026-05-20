from __future__ import annotations

import tempfile
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from fastapi import APIRouter, HTTPException
from yt_dlp.utils import DownloadError

from app.core.storage.client import get_storage
from app.youtube.application.use_cases import GetCachedTranscription, TranslateYouTubeVideo
from app.youtube.domain.exceptions import DownloadFailedError, TranscriptionFailedError
from app.youtube.domain.sentences import build_sentences
from app.youtube.infrastructure.downloader import YtDlpAudioDownloader
from app.youtube.infrastructure.schemas import (
    SentencesResponse,
    WhisperWord,
    YouTubeTranslateRequest,
    YouTubeTranslateResponse,
)
from app.youtube.infrastructure.transcriber import WhisperTranscriber

router = APIRouter(tags=["youtube"])


def _normalize_youtube_video_id(youtube_url: str) -> Optional[str]:
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


def get_cached_transcription(video_id: str) -> Optional[Dict[str, Any]]:
    return GetCachedTranscription(get_storage()).execute(video_id)


def _build_translate_response(
    data: Dict[str, Any], include_words: bool
) -> YouTubeTranslateResponse:
    words: List[WhisperWord] = []
    if include_words:
        words = [
            WhisperWord(word=w["word"], start=w["start"], end=w["end"])
            for w in data.get("words", [])
        ]
    return YouTubeTranslateResponse(
        title=data["title"],
        video_id=data["video_id"],
        source_language=data.get("language"),
        translated_text=data.get("text", ""),
        words=words,
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
        sentences=build_sentences(transcription),
    )


@router.post("/youtube/translate", response_model=YouTubeTranslateResponse)
def translate_youtube_video(request: YouTubeTranslateRequest) -> YouTubeTranslateResponse:
    video_id = _normalize_youtube_video_id(str(request.youtube_url))
    storage = get_storage()
    if video_id:
        cached = get_cached_transcription(video_id)
        if cached:
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
        raise HTTPException(
            status_code=400, detail=f"YouTube download failed: {exc}"
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail="ffmpeg is required by yt-dlp/Whisper but was not found on the server.",
        ) from exc
    except TranscriptionFailedError as exc:
        raise HTTPException(status_code=500, detail=f"Whisper failed: {exc}") from exc

    return _build_translate_response(data, request.include_words)
