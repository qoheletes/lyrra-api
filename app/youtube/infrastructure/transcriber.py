from __future__ import annotations

from typing import Optional

import openai

from app.core.config import settings
from app.youtube.domain.exceptions import TranscriptionFailedError
from app.youtube.domain.models import SpeakerSegment, TranscriptionResult, WordTimestamp


class WhisperTranscriber:
    def transcribe(
        self,
        audio_path: str,
        model_name: str,
        source_language: Optional[str],
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
