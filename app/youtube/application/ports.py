from __future__ import annotations

from typing import Optional, Protocol

from app.youtube.domain.models import AudioDownloadResult, TranscriptionResult


class AudioDownloader(Protocol):
    def download(self, youtube_url: str, output_dir: str) -> AudioDownloadResult:
        ...


class Transcriber(Protocol):
    def transcribe(
        self,
        audio_path: str,
        model_name: str,
        source_language: Optional[str],
    ) -> TranscriptionResult:
        ...
