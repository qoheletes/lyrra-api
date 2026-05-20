from __future__ import annotations

import json
from typing import Any, Dict, Optional

from app.core.storage.client import StorageAdapter
from app.youtube.application.ports import AudioDownloader, Transcriber
from app.youtube.domain.models import TranscriptionResult
from app.youtube.domain.sentences import build_sentences


def _transcription_key(video_id: str) -> str:
    return f"transcriptions/{video_id}.json"


def _sentences_key(video_id: str) -> str:
    return f"transcriptions/{video_id}_sentences.json"


class GetCachedTranscription:
    def __init__(self, storage: StorageAdapter) -> None:
        self._storage = storage

    def execute(self, video_id: str) -> Optional[Dict[str, Any]]:
        data = self._storage.download(_transcription_key(video_id))
        if data is None:
            return None
        return json.loads(data)


class TranslateYouTubeVideo:
    def __init__(
        self,
        downloader: AudioDownloader,
        transcriber: Transcriber,
        storage: StorageAdapter,
    ) -> None:
        self._downloader = downloader
        self._transcriber = transcriber
        self._storage = storage

    def execute(
        self,
        youtube_url: str,
        model_name: str,
        source_language: Optional[str],
        output_dir: str,
    ) -> Dict[str, Any]:
        audio = self._downloader.download(youtube_url, output_dir)
        transcription = self._transcriber.transcribe(
            audio.audio_path, model_name, source_language
        )
        self._save_transcription(audio, transcription)
        self._save_sentences(audio.video_id, transcription)
        return {
            "video_id": audio.video_id,
            "title": audio.title,
            "duration_ms": audio.duration_ms,
            "source_url": audio.source_url,
            "language": transcription.language,
            "text": transcription.text,
            "words": [
                {"word": w.word, "start": w.start, "end": w.end}
                for w in transcription.words
            ],
        }

    def _save_transcription(self, audio: Any, transcription: TranscriptionResult) -> None:
        payload = {
            "video_id": audio.video_id,
            "title": audio.title,
            "duration_ms": audio.duration_ms,
            "source_url": audio.source_url,
            "language": transcription.language,
            "text": transcription.text,
            "words": [
                {"word": w.word, "start": w.start, "end": w.end}
                for w in transcription.words
            ],
        }
        key = _transcription_key(audio.video_id)
        url = self._storage.upload(key, json.dumps(payload, indent=2).encode())
        print(f"[transcribe] saved to {url}")

    def _save_sentences(self, video_id: str, transcription: TranscriptionResult) -> None:
        raw = {
            "text": transcription.text,
            "words": [
                {"word": w.word, "start": w.start, "end": w.end}
                for w in transcription.words
            ],
        }
        sentences = build_sentences(raw)
        payload = {
            "video_id": video_id,
            "language": transcription.language,
            "sentences": [
                {
                    "text": s.text,
                    "start": s.start,
                    "end": s.end,
                    "words": [{"word": w.word, "start": w.start, "end": w.end} for w in s.words],
                }
                for s in sentences
            ],
        }
        key = _sentences_key(video_id)
        url = self._storage.upload(key, json.dumps(payload, indent=2).encode())
        print(f"[transcribe] sentences saved to {url}")
