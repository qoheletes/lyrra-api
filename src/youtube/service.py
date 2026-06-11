from __future__ import annotations

import gzip
import json
import re
from typing import TYPE_CHECKING, Any, Protocol

from src.youtube.schemas import Sentence, SentenceWord

if TYPE_CHECKING:
    from src.storage.client import StorageAdapter
    from src.youtube.models import (
        AudioDownloadResult,
        TranscriptionResult,
        VideoSearchResults,
    )

# ---------------------------------------------------------------------------
# Ports — the contracts the use cases depend on (implemented in client.py)
# ---------------------------------------------------------------------------


class AudioDownloader(Protocol):
    def download(self, youtube_url: str, output_dir: str) -> AudioDownloadResult: ...


class Transcriber(Protocol):
    def transcribe(
        self,
        audio_path: str,
        model_name: str,
        source_language: str | None,
    ) -> TranscriptionResult: ...


class Translator(Protocol):
    def translate(self, text: str, target_language: str) -> str: ...


class YouTubeSearcher(Protocol):
    def search(
        self,
        query: str,
        max_results: int,
        page_token: str | None,
    ) -> VideoSearchResults: ...


# ---------------------------------------------------------------------------
# Storage keys and serialization
# ---------------------------------------------------------------------------

_GZIP_MAGIC = b"\x1f\x8b"


def _sentences_key(video_id: str) -> str:
    return f"transcriptions/{video_id}.json"


def _translation_key(video_id: str, target_language: str) -> str:
    return f"transcriptions/{video_id}_translated_{target_language}.json"


def _compress_json(payload: dict[str, Any]) -> bytes:
    # mtime=0 keeps the gzip output deterministic for identical payloads
    return gzip.compress(json.dumps(payload, separators=(",", ":")).encode(), mtime=0)


def _decompress_json(data: bytes) -> dict[str, Any]:
    if data[:2] == _GZIP_MAGIC:
        data = gzip.decompress(data)
    return json.loads(data)


# ---------------------------------------------------------------------------
# Sentence segmentation
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9']+", text.lower())


def build_sentences(transcription: dict[str, Any]) -> list[Sentence]:
    text = transcription.get("text", "").strip()
    raw_words = transcription.get("words", [])

    if not text or not raw_words:
        return []

    sentence_texts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])", text)

    sentences: list[Sentence] = []
    word_idx = 0

    for sentence_text in sentence_texts:
        sentence_text = sentence_text.strip()
        if not sentence_text:
            continue

        tokens = _tokenize(sentence_text)
        if not tokens:
            continue

        consumed: list[SentenceWord] = []
        remaining = len(tokens)
        i = word_idx

        while remaining > 0 and i < len(raw_words):
            w = raw_words[i]
            word_tokens = _tokenize(w["word"])
            if word_tokens:
                consumed.append(SentenceWord(word=w["word"], start=w["start"], end=w["end"]))
                remaining -= len(word_tokens)
            i += 1

        word_idx = i

        if not consumed:
            continue

        sentences.append(
            Sentence(
                text=sentence_text,
                start=consumed[0].start,
                end=consumed[-1].end,
                words=consumed,
            )
        )

    return sentences


# ---------------------------------------------------------------------------
# Use cases
# ---------------------------------------------------------------------------


class GetCachedTranscription:
    def __init__(self, storage: StorageAdapter) -> None:
        self._storage = storage

    def execute(self, video_id: str) -> dict[str, Any] | None:
        key = _sentences_key(video_id)
        data = self._storage.download(key)
        if data is None:
            return None
        payload = _decompress_json(data)
        sentences = payload.get("sentences", [])
        return {
            "video_id": payload["video_id"],
            "title": payload.get("title", ""),
            "duration_ms": payload.get("duration_ms"),
            "source_url": payload.get("source_url"),
            "language": payload.get("language"),
            "text": " ".join(s["text"] for s in sentences),
            "transcription_url": self._storage.get_public_url(key),
            "words": [w for s in sentences for w in s["words"]],
            "segments": [],
            "sentences": sentences,
        }


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
        source_language: str | None,
        output_dir: str,
    ) -> dict[str, Any]:
        audio = self._downloader.download(youtube_url, output_dir)
        transcription = self._transcriber.transcribe(audio.audio_path, model_name, source_language)
        transcription_url = self._save_sentences(audio, transcription)
        return {
            "video_id": audio.video_id,
            "title": audio.title,
            "duration_ms": audio.duration_ms,
            "source_url": audio.source_url,
            "language": transcription.language,
            "text": transcription.text,
            "transcription_url": transcription_url,
            "words": [
                {"word": w.word, "start": w.start, "end": w.end} for w in transcription.words
            ],
            "segments": [
                {"speaker": s.speaker, "text": s.text, "start": s.start, "end": s.end}
                for s in transcription.segments
            ],
        }

    def _save_sentences(self, audio: Any, transcription: TranscriptionResult) -> str:
        raw = {
            "text": transcription.text,
            "words": [
                {"word": w.word, "start": w.start, "end": w.end} for w in transcription.words
            ],
        }
        sentences = build_sentences(raw)
        payload = {
            "video_id": audio.video_id,
            "title": audio.title,
            "duration_ms": audio.duration_ms,
            "source_url": audio.source_url,
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
        key = _sentences_key(audio.video_id)
        url = self._storage.upload(
            key,
            _compress_json(payload),
            content_type="application/json",
            content_encoding="gzip",
        )
        print(f"[transcribe] sentences saved to {url}")
        return url


class TranslateTranscription:
    """Loads the cached sentence payload from storage and saves a translated version."""

    def __init__(self, storage: StorageAdapter, translator: Translator) -> None:
        self._storage = storage
        self._translator = translator

    def execute(self, video_id: str, target_language: str) -> None:
        data = self._storage.download(_sentences_key(video_id))
        if data is None:
            print(f"[translate] no cached transcription for {video_id!r}, skipping")
            return
        sentences_payload = _decompress_json(data)
        text = " ".join(s["text"] for s in sentences_payload.get("sentences", []))
        translated_text = self._translator.translate(text, target_language)
        payload = {
            **sentences_payload,
            "translated_text": translated_text,
            "target_language": target_language,
        }
        key = _translation_key(video_id, target_language)
        url = self._storage.upload(
            key,
            _compress_json(payload),
            content_type="application/json",
            content_encoding="gzip",
        )
        print(f"[translate] saved {target_language!r} translation to {url}")


class SearchYouTubeVideos:
    def __init__(self, searcher: YouTubeSearcher) -> None:
        self._searcher = searcher

    def execute(
        self,
        query: str,
        max_results: int = 10,
        page_token: str | None = None,
    ) -> VideoSearchResults:
        return self._searcher.search(query, max_results, page_token)
