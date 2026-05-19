"""Tests for build_sentences and GET /youtube/transcribe/{video_id}/sentences."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.youtube.sentences import build_sentences

TRANSCRIPTION_FILE = Path(__file__).parent.parent / "data" / "transcriptions" / "rkd-pdjVZVM.json"

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def transcription():
    if not TRANSCRIPTION_FILE.exists():
        pytest.skip("Transcription fixture not found")
    return json.loads(TRANSCRIPTION_FILE.read_text())


@pytest.fixture(scope="module")
def sentences(transcription):
    return build_sentences(transcription)


# ---------------------------------------------------------------------------
# Unit tests for build_sentences
# ---------------------------------------------------------------------------

def test_returns_non_empty_list(sentences):
    assert len(sentences) > 0


def test_first_sentence_text(sentences):
    first = sentences[0].text
    assert first.startswith("As someone who struggles")
    assert first.endswith("changing my life.")


def test_first_sentence_timestamps(sentences):
    first = sentences[0]
    assert first.start == pytest.approx(0.0, abs=0.1)
    assert first.end == pytest.approx(4.8, abs=0.5)


def test_first_sentence_has_words(sentences):
    assert len(sentences[0].words) > 0


def test_hello_sentence(sentences):
    hello = next((s for s in sentences if s.text.startswith("Hello")), None)
    assert hello is not None
    assert len(hello.words) == 2


def test_word_timestamps_within_sentence_bounds(sentences):
    for sentence in sentences:
        for word in sentence.words:
            assert word.start >= sentence.start - 0.01
            assert word.end <= sentence.end + 0.01


def test_total_word_count_close_to_raw(transcription, sentences):
    raw_count = len(transcription["words"])
    sentence_word_count = sum(len(s.words) for s in sentences)
    assert abs(sentence_word_count - raw_count) <= 5


def test_sentences_monotonically_increasing(sentences):
    for i in range(1, len(sentences)):
        assert sentences[i].start >= sentences[i - 1].start


def test_empty_transcription():
    assert build_sentences({}) == []
    assert build_sentences({"text": "", "words": []}) == []


def test_single_sentence():
    result = build_sentences({
        "text": "Hello world.",
        "words": [
            {"word": "Hello", "start": 0.0, "end": 0.5},
            {"word": "world", "start": 0.5, "end": 1.0},
        ],
    })
    assert len(result) == 1
    assert result[0].text == "Hello world."
    assert result[0].start == 0.0
    assert result[0].end == 1.0
    assert len(result[0].words) == 2


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------

FAKE_TRANSCRIPTION = {
    "video_id": "abc123",
    "language": "english",
    "text": "Hello world. Goodbye world.",
    "words": [
        {"word": "Hello", "start": 0.0, "end": 0.5},
        {"word": "world", "start": 0.5, "end": 1.0},
        {"word": "Goodbye", "start": 1.5, "end": 2.0},
        {"word": "world", "start": 2.0, "end": 2.5},
    ],
}


def test_endpoint_returns_sentences():
    with patch("app.youtube.router.get_cached_transcription", return_value=FAKE_TRANSCRIPTION):
        resp = client.get("/youtube/transcribe/abc123/sentences")

    assert resp.status_code == 200
    body = resp.json()
    assert body["video_id"] == "abc123"
    assert body["language"] == "english"
    assert len(body["sentences"]) == 2


def test_endpoint_sentence_shape():
    with patch("app.youtube.router.get_cached_transcription", return_value=FAKE_TRANSCRIPTION):
        resp = client.get("/youtube/transcribe/abc123/sentences")

    first = resp.json()["sentences"][0]
    assert first["text"] == "Hello world."
    assert first["start"] == pytest.approx(0.0)
    assert first["end"] == pytest.approx(1.0)
    assert len(first["words"]) == 2
    assert first["words"][0]["word"] == "Hello"


def test_endpoint_404_on_missing_video():
    with patch("app.youtube.router.get_cached_transcription", return_value=None):
        resp = client.get("/youtube/transcribe/does-not-exist/sentences")

    assert resp.status_code == 404
