import re
from typing import Any, Dict, List

from pydantic import BaseModel


class SentenceWord(BaseModel):
    word: str
    start: float
    end: float


class Sentence(BaseModel):
    text: str
    start: float
    end: float
    words: List[SentenceWord]


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[A-Za-z0-9']+", text.lower())


def build_sentences(transcription: Dict[str, Any]) -> List[Sentence]:
    text = transcription.get("text", "").strip()
    raw_words = transcription.get("words", [])

    if not text or not raw_words:
        return []

    sentence_texts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])", text)

    sentences: List[Sentence] = []
    word_idx = 0

    for sentence_text in sentence_texts:
        sentence_text = sentence_text.strip()
        if not sentence_text:
            continue

        tokens = _tokenize(sentence_text)
        if not tokens:
            continue

        consumed: List[SentenceWord] = []
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

        sentences.append(Sentence(
            text=sentence_text,
            start=consumed[0].start,
            end=consumed[-1].end,
            words=consumed,
        ))

    return sentences
