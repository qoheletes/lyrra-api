from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import openai
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from src.config import settings
from src.youtube.exceptions import DownloadFailedError, TranscriptionFailedError
from src.youtube.models import (
    AudioDownloadResult,
    SpeakerSegment,
    TranscriptionResult,
    VideoSearchResult,
    VideoSearchResults,
    WordTimestamp,
)

_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def _duration_to_ms(duration_seconds: Any) -> int | None:
    if duration_seconds is None:
        return None
    try:
        return int(float(duration_seconds) * 1000)
    except (TypeError, ValueError):
        return None


class YtDlpAudioDownloader:
    def download(self, youtube_url: str, output_dir: str) -> AudioDownloadResult:
        output_template = os.path.join(output_dir, "%(id)s.%(ext)s")
        ydl_opts: dict = {
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
        if settings.yt_dlp_cookies_file:
            ydl_opts["cookiefile"] = settings.yt_dlp_cookies_file
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                requested = info.get("requested_downloads")
                if requested:
                    downloaded_path = Path(requested[0]["filepath"])
                else:
                    downloaded_path = Path(ydl.prepare_filename(info))
        except DownloadError as exc:
            raise DownloadFailedError(str(exc)) from exc

        result = AudioDownloadResult(
            video_id=info.get("id", ""),
            title=info.get("title", "Unknown title"),
            audio_path=str(downloaded_path),
            duration_ms=_duration_to_ms(info.get("duration")),
        )
        print(
            f"[audio] downloaded: id={result.video_id!r}"
            f" title={result.title!r}"
            f" duration_ms={result.duration_ms}"
            f" path={result.audio_path}"
        )
        return result


class WhisperTranscriber:
    def transcribe(
        self,
        audio_path: str,
        model_name: str,
        source_language: str | None,
    ) -> TranscriptionResult:
        client = openai.OpenAI(api_key=settings.openai_api_key)
        try:
            with open(audio_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    file=audio_file,
                    model=model_name,
                    response_format="verbose_json",
                    timestamp_granularities=["word", "segment"],
                )
        except (RuntimeError, openai.OpenAIError) as exc:
            raise TranscriptionFailedError(str(exc)) from exc

        words = [
            WordTimestamp(word=w.word, start=w.start, end=w.end)
            for w in (getattr(response, "words", None) or [])
        ]
        segments = [
            SpeakerSegment(
                speaker=getattr(seg, "speaker", None) or "SPEAKER_0",
                text=seg.text,
                start=seg.start,
                end=seg.end,
            )
            for seg in (getattr(response, "segments", None) or [])
        ]
        language = getattr(response, "language", None) or ""
        print(
            f"[transcribe] language={language!r}"
            f" words={len(words)} segments={len(segments)}"
            f"\n{response.text.strip()}"
        )
        return TranscriptionResult(
            language=language,
            text=response.text.strip(),
            words=words,
            segments=segments,
        )


class OpenAITranslator:
    def translate(self, text: str, target_language: str) -> str:
        client = openai.OpenAI(api_key=settings.openai_api_key)
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"Translate the following text to {target_language}. "
                            "Return only the translated text, no explanations."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
            )
        except openai.OpenAIError as exc:
            raise RuntimeError(f"Translation failed: {exc}") from exc
        return response.choices[0].message.content or ""


class YouTubeAPISearcher:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def search(
        self,
        query: str,
        max_results: int,
        page_token: str | None,
    ) -> VideoSearchResults:
        params: dict = {
            "part": "snippet",
            "type": "video",
            "q": query,
            "maxResults": max_results,
            "videoDuration": "medium",
            "key": self._api_key,
        }
        if page_token:
            params["pageToken"] = page_token

        url = f"{_SEARCH_URL}?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url) as resp:
            body = json.loads(resp.read().decode())

        results = [
            VideoSearchResult(
                video_id=item["id"]["videoId"],
                title=item["snippet"]["title"],
                description=item["snippet"]["description"],
                channel_title=item["snippet"]["channelTitle"],
                published_at=item["snippet"]["publishedAt"],
                thumbnail_url=(
                    item["snippet"].get("thumbnails", {}).get("medium", {}).get("url")
                    or item["snippet"].get("thumbnails", {}).get("default", {}).get("url")
                ),
            )
            for item in body.get("items", [])
        ]

        return VideoSearchResults(
            query=query,
            results=results,
            next_page_token=body.get("nextPageToken"),
        )
