"""Transcriptions are stored as a single gzip-compressed sentence JSON per video."""

import gzip
import json

from src.youtube.models import AudioDownloadResult, TranscriptionResult, WordTimestamp
from src.youtube.service import (
    GetCachedTranscription,
    TranslateTranscription,
    TranslateYouTubeVideo,
    _compress_json,
    _decompress_json,
    _sentences_key,
)


class FakeStorage:
    def __init__(self):
        self.objects: dict[str, bytes] = {}
        self.uploads: list[dict] = []

    def upload(self, key, data, content_type=None, content_encoding=None):
        self.objects[key] = data
        self.uploads.append(
            {"key": key, "content_type": content_type, "content_encoding": content_encoding}
        )
        return self.get_public_url(key)

    def download(self, key):
        return self.objects.get(key)

    def delete(self, key):
        self.objects.pop(key, None)

    def get_public_url(self, key):
        return f"https://files.example.com/{key}"


class FakeDownloader:
    def download(self, youtube_url, output_dir):
        return AudioDownloadResult(
            video_id="vid123",
            title="A Test Video",
            audio_path="/tmp/audio.mp3",
            duration_ms=4000,
            source_url=youtube_url,
        )


class FakeTranscriber:
    def transcribe(self, audio_path, model_name, source_language):
        return TranscriptionResult(
            language="en",
            text="Hello world. This is fine.",
            words=[
                WordTimestamp(word="Hello", start=0.0, end=0.5),
                WordTimestamp(word="world.", start=0.5, end=1.0),
                WordTimestamp(word="This", start=1.5, end=2.0),
                WordTimestamp(word="is", start=2.0, end=2.2),
                WordTimestamp(word="fine.", start=2.2, end=2.8),
            ],
        )


class FakeTranslator:
    def translate(self, text, target_language):
        return f"[{target_language}] {text}"


def _transcribe(storage):
    uc = TranslateYouTubeVideo(FakeDownloader(), FakeTranscriber(), storage)
    return uc.execute("https://youtu.be/vid123", "whisper-1", None, "/tmp")


def test_json_gzip_roundtrip():
    payload = {"video_id": "vid123", "sentences": [{"text": "Hi"}]}
    data = _compress_json(payload)
    assert data[:2] == b"\x1f\x8b"
    assert _decompress_json(data) == payload


def test_transcribe_stores_single_compressed_sentence_file():
    storage = FakeStorage()
    _transcribe(storage)

    assert list(storage.objects) == ["transcriptions/vid123/transcription.json"]
    upload = storage.uploads[0]
    assert upload["content_type"] == "application/json"
    assert upload["content_encoding"] == "gzip"

    raw = storage.objects["transcriptions/vid123/transcription.json"]
    payload = json.loads(gzip.decompress(raw))
    assert payload["video_id"] == "vid123"
    assert payload["title"] == "A Test Video"
    assert payload["language"] == "en"
    # sentence JSON only: no raw transcription fields at the top level
    assert "text" not in payload
    assert "words" not in payload
    assert "segments" not in payload
    assert [s["text"] for s in payload["sentences"]] == ["Hello world.", "This is fine."]
    assert all(s["words"] for s in payload["sentences"])


def test_get_cached_transcription_derives_response_from_sentences():
    storage = FakeStorage()
    _transcribe(storage)

    cached = GetCachedTranscription(storage).execute("vid123")
    assert cached is not None
    assert cached["video_id"] == "vid123"
    assert cached["title"] == "A Test Video"
    assert cached["text"] == "Hello world. This is fine."
    assert cached["transcription_url"] == storage.get_public_url(_sentences_key("vid123"))
    assert [w["word"] for w in cached["words"]] == ["Hello", "world.", "This", "is", "fine."]
    assert len(cached["sentences"]) == 2


def test_get_cached_transcription_returns_none_when_missing():
    assert GetCachedTranscription(FakeStorage()).execute("missing") is None


def test_translate_transcription_reads_and_writes_compressed_sentence_json():
    storage = FakeStorage()
    _transcribe(storage)

    TranslateTranscription(storage, FakeTranslator()).execute("vid123", "es")

    key = "transcriptions/vid123/es.json"
    assert key in storage.objects
    payload = json.loads(gzip.decompress(storage.objects[key]))
    assert payload["translated_text"] == "[es] Hello world. This is fine."
    assert payload["target_language"] == "es"
    assert [s["text"] for s in payload["sentences"]] == ["Hello world.", "This is fine."]
