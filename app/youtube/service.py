import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

import openai
from yt_dlp import YoutubeDL

from app.config import settings
from app.storage.client import get_storage
from app.youtube.schemas import WhisperWord, YouTubeTranslateResponse
from app.youtube.sentences import build_sentences


def normalize_youtube_video_id(youtube_url: str) -> Optional[str]:
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


def _duration_to_ms(duration_seconds: Any) -> Optional[int]:
    if duration_seconds is None:
        return None
    try:
        return int(float(duration_seconds) * 1000)
    except (TypeError, ValueError):
        return None


def download_youtube_audio(youtube_url: str, output_dir: str) -> Dict[str, Any]:
    output_template = os.path.join(output_dir, "%(id)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        requested = info.get("requested_downloads")
        if requested:
            downloaded_path = Path(requested[0]["filepath"])
        else:
            downloaded_path = Path(ydl.prepare_filename(info))

    audio_info = {
        "title": info.get("title", "Unknown title"),
        "video_id": info.get("id", ""),
        "audio_path": str(downloaded_path),
        "duration_ms": _duration_to_ms(info.get("duration")),
    }
    print(
        f"[audio] downloaded: id={audio_info['video_id']!r}"
        f" title={audio_info['title']!r}"
        f" duration_ms={audio_info['duration_ms']}"
        f" path={audio_info['audio_path']}"
    )
    return audio_info


def translate_audio(
    audio_path: str,
    model_name: str,
    source_language: Optional[str],
) -> Dict[str, Any]:
    client = openai.OpenAI(api_key=settings.openai_api_key)
    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            file=audio_file,
            model=model_name,
            response_format="verbose_json",
            timestamp_granularities=["word"],
        )
    words = [
        {"word": w.word, "start": w.start, "end": w.end}
        for w in (response.words or [])
    ]
    return {
        "language": response.language,
        "text": response.text.strip(),
        "words": words,
    }


def _transcription_key(video_id: str) -> str:
    return f"transcriptions/{video_id}.json"


def _sentences_key(video_id: str) -> str:
    return f"transcriptions/{video_id}_sentences.json"


def get_cached_transcription(video_id: str) -> Optional[Dict[str, Any]]:
    data = get_storage().download(_transcription_key(video_id))
    if data is None:
        return None
    return json.loads(data)


def save_transcription(
    video_data: Dict[str, Any],
    transcription: Dict[str, Any],
) -> str:
    video_id = video_data["video_id"]
    payload = {
        "video_id": video_id,
        "title": video_data["title"],
        "duration_ms": video_data.get("duration_ms"),
        "source_url": video_data.get("source_url"),
        "language": transcription.get("language"),
        "text": transcription.get("text", "").strip(),
        "words": [
            {
                "word": w["word"],
                "start": w["start"],
                "end": w["end"],
            }
            for w in transcription.get("words", [])
        ],
    }
    key = _transcription_key(video_id)
    url = get_storage().upload(key, json.dumps(payload, indent=2).encode())
    print(f"[transcribe] saved to {url}")
    return url


def save_sentences(
    video_id: str,
    transcription: Dict[str, Any],
) -> str:
    sentences = build_sentences(transcription)
    payload = {
        "video_id": video_id,
        "language": transcription.get("language"),
        "sentences": [
            {
                "text": s.text,
                "start": s.start,
                "end": s.end,
                "words": [
                    {"word": w.word, "start": w.start, "end": w.end}
                    for w in s.words
                ],
            }
            for s in sentences
        ],
    }
    key = _sentences_key(video_id)
    url = get_storage().upload(key, json.dumps(payload, indent=2).encode())
    print(f"[transcribe] sentences saved to {url}")
    return url


def build_translate_response(
    data: Dict[str, Any], include_words: bool
) -> YouTubeTranslateResponse:
    words: List[WhisperWord] = []
    if include_words:
        words = [
            WhisperWord(
                word=w["word"],
                start=w["start"],
                end=w["end"],
            )
            for w in data.get("words", [])
        ]

    return YouTubeTranslateResponse(
        title=data["title"],
        video_id=data["video_id"],
        source_language=data.get("language"),
        translated_text=data.get("text", ""),
        words=words,
    )
