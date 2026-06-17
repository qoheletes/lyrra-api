"""End-to-end test of the transcribe flow through the FastAPI HTTP layer.

This drives the real app (router → use cases → storage serialization) over HTTP
via TestClient. Only the true external edges are faked: audio download (yt-dlp),
transcription (Whisper), translation (OpenAI), and R2 storage. Everything in
between — request validation, video-id normalization, sentence segmentation,
gzip+JSON storage, caching, and background translation — runs for real.
"""

import gzip
import json

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.youtube.models import AudioDownloadResult, TranscriptionResult, WordTimestamp

VIDEO_ID = "dQw4w9WgXcQ"
YOUTUBE_URL = f"https://www.youtube.com/watch?v={VIDEO_ID}"
SENTENCES_KEY = f"transcriptions/{VIDEO_ID}/transcription.json"


class FakeStorage:
    """In-memory stand-in for R2, shared across requests in a single test."""

    def __init__(self):
        self.objects: dict[str, bytes] = {}

    def upload(self, key, data, content_type=None, content_encoding=None):
        self.objects[key] = data
        return self.get_public_url(key)

    def download(self, key):
        return self.objects.get(key)

    def delete(self, key):
        self.objects.pop(key, None)

    def get_public_url(self, key):
        return f"https://files.example.com/{key}"


class FakeDownloader:
    def __init__(self):
        self.calls = 0

    def download(self, youtube_url, output_dir):
        self.calls += 1
        return AudioDownloadResult(
            video_id=VIDEO_ID,
            title="Never Gonna Give You Up",
            audio_path=f"{output_dir}/audio.mp3",
            duration_ms=3000,
            source_url=youtube_url,
        )


class FakeTranscriber:
    def __init__(self):
        self.calls = 0

    def transcribe(self, audio_path, model_name, source_language):
        self.calls += 1
        return TranscriptionResult(
            language="en",
            text="Never gonna give you up. Never gonna let you down.",
            words=[
                WordTimestamp(word="Never", start=0.0, end=0.3),
                WordTimestamp(word="gonna", start=0.3, end=0.6),
                WordTimestamp(word="give", start=0.6, end=0.9),
                WordTimestamp(word="you", start=0.9, end=1.1),
                WordTimestamp(word="up.", start=1.1, end=1.5),
                WordTimestamp(word="Never", start=1.6, end=1.9),
                WordTimestamp(word="gonna", start=1.9, end=2.2),
                WordTimestamp(word="let", start=2.2, end=2.4),
                WordTimestamp(word="you", start=2.4, end=2.6),
                WordTimestamp(word="down.", start=2.6, end=3.0),
            ],
        )


class FakeTranslator:
    def __init__(self):
        self.calls = 0

    def translate(self, text, target_language):
        self.calls += 1
        return f"[{target_language}] {text}"


@pytest.fixture
def e2e(monkeypatch):
    """Wire the app's external edges to in-memory fakes and yield a live client."""
    storage = FakeStorage()
    downloader = FakeDownloader()
    transcriber = FakeTranscriber()
    translator = FakeTranslator()

    monkeypatch.setattr("src.youtube.router.get_storage", lambda: storage)
    monkeypatch.setattr("src.youtube.router.YtDlpAudioDownloader", lambda: downloader)
    monkeypatch.setattr("src.youtube.router.WhisperTranscriber", lambda: transcriber)
    monkeypatch.setattr("src.youtube.router.OpenAITranslator", lambda: translator)

    # No `with` block: the transcribe flow never touches the DB, so we skip the
    # lifespan (Base.metadata.create_all) that would require a live Postgres.
    # TestClient still runs background tasks synchronously per request.
    client = TestClient(app)
    return client, storage, downloader, transcriber, translator


def test_transcribe_fresh_video_returns_response_and_stores_one_gzip_object(e2e):
    client, storage, downloader, transcriber, _ = e2e

    resp = client.post("/youtube/translate", json={"youtube_url": YOUTUBE_URL})

    assert resp.status_code == 200
    body = resp.json()
    assert body["video_id"] == VIDEO_ID
    assert body["title"] == "Never Gonna Give You Up"
    assert body["source_language"] == "en"
    assert body["translated_text"] == "Never gonna give you up. Never gonna let you down."
    assert body["transcription_url"] == f"https://files.example.com/{SENTENCES_KEY}"
    # include_words defaults to True
    assert [w["word"] for w in body["words"]][:3] == ["Never", "gonna", "give"]

    # The flow actually downloaded and transcribed exactly once.
    assert downloader.calls == 1
    assert transcriber.calls == 1

    # Exactly one object persisted: gzip-compressed sentence JSON.
    assert list(storage.objects) == [SENTENCES_KEY]
    raw = storage.objects[SENTENCES_KEY]
    assert raw[:2] == b"\x1f\x8b"
    payload = json.loads(gzip.decompress(raw))
    assert payload["video_id"] == VIDEO_ID
    assert [s["text"] for s in payload["sentences"]] == [
        "Never gonna give you up.",
        "Never gonna let you down.",
    ]
    # Sentence JSON only — no raw transcription dump at the top level.
    assert "text" not in payload
    assert "words" not in payload


def test_second_transcribe_is_served_from_cache(e2e):
    client, _, downloader, transcriber, _ = e2e

    first = client.post("/youtube/translate", json={"youtube_url": YOUTUBE_URL})
    second = client.post("/youtube/translate", json={"youtube_url": YOUTUBE_URL})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["video_id"] == second.json()["video_id"]
    # Cache hit: no second download/transcription.
    assert downloader.calls == 1
    assert transcriber.calls == 1


def test_sentences_endpoint_returns_stored_sentences_after_transcribe(e2e):
    client, _, _, _, _ = e2e

    client.post("/youtube/translate", json={"youtube_url": YOUTUBE_URL})
    resp = client.get(f"/youtube/{VIDEO_ID}/transcript")

    assert resp.status_code == 200
    body = resp.json()
    assert body["video_id"] == VIDEO_ID
    assert body["language"] == "en"
    assert [s["text"] for s in body["sentences"]] == [
        "Never gonna give you up.",
        "Never gonna let you down.",
    ]
    first_sentence = body["sentences"][0]
    assert first_sentence["start"] == 0.0
    assert first_sentence["words"][0]["word"] == "Never"


def test_sentences_endpoint_404_when_not_transcribed(e2e):
    client, _, _, _, _ = e2e

    resp = client.get("/youtube/unknownvid/transcript")

    assert resp.status_code == 404
    assert "unknownvid" in resp.json()["detail"]


def test_target_language_runs_background_translation_and_stores_translated_json(e2e):
    client, storage, _, _, translator = e2e

    resp = client.post(
        "/youtube/translate",
        json={"youtube_url": YOUTUBE_URL, "target_language": "es"},
    )

    assert resp.status_code == 200
    # Background task runs before TestClient returns the response.
    assert translator.calls == 1
    translated_key = f"transcriptions/{VIDEO_ID}/es.json"
    assert translated_key in storage.objects
    payload = json.loads(gzip.decompress(storage.objects[translated_key]))
    assert payload["target_language"] == "es"
    assert payload["translated_text"] == (
        "[es] Never gonna give you up. Never gonna let you down."
    )
