from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from app.youtube.domain.exceptions import DownloadFailedError
from app.youtube.domain.models import AudioDownloadResult


class YtDlpAudioDownloader:
    def download(self, youtube_url: str, output_dir: str) -> AudioDownloadResult:
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


def _duration_to_ms(duration_seconds: Any) -> Optional[int]:
    if duration_seconds is None:
        return None
    try:
        return int(float(duration_seconds) * 1000)
    except (TypeError, ValueError):
        return None
