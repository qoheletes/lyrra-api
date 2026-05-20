from __future__ import annotations

from typing import Optional

import openai

from app.core.config import settings
from app.youtube.domain.exceptions import TranscriptionFailedError
from app.youtube.domain.models import TranscriptionResult, WordTimestamp


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
                    timestamp_granularities=["word"],
                )
        except RuntimeError as exc:
            raise TranscriptionFailedError(str(exc)) from exc
        words = [
            WordTimestamp(word=w.word, start=w.start, end=w.end)
            for w in (response.words or [])
        ]
        print(
            f"[translate] language={response.language!r}"
            f" words={len(words)}"
            f"\n{response.text.strip()}"
        )
        return TranscriptionResult(
            language=response.language,
            text=response.text.strip(),
            words=words,
        )
