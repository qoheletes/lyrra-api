# YouTube

Accepts a YouTube URL, downloads the audio, runs Whisper transcription/translation to English, and caches the result in object storage for subsequent requests.

## Module layout

Flat, domain-scoped modules (see `docs/project-structure.md`). This domain has no database — its state lives in object storage.

- `models.py` — pure data classes (`AudioDownloadResult`, `TranscriptionResult`, `WordTimestamp`, `SpeakerSegment`, `VideoSearchResult(s)`); no I/O
- `schemas.py` — request/response Pydantic models, plus `Sentence`/`SentenceWord`
- `service.py` — the ports (`AudioDownloader`, `Transcriber`, `Translator`, `YouTubeSearcher` Protocols), the use cases (`GetCachedTranscription`, `TranslateYouTubeVideo`, `TranslateTranscription`, `SearchYouTubeVideos`), and `build_sentences`
- `client.py` — concrete adapters that implement the ports: `YtDlpAudioDownloader`, `WhisperTranscriber`, `OpenAITranslator`, `YouTubeAPISearcher`
- `router.py` — FastAPI router (`/youtube/*`); wires adapters into use cases
- `exceptions.py` — `DownloadFailedError`, `TranscriptionFailedError`

## Data Flow

1. Router receives `YouTubeTranslateRequest` and normalizes the URL to a `VideoId`
2. `GetCachedTranscription` checks object storage; returns the cached `Transcription` if present
3. If not cached, `TranslateYouTubeVideo` calls `AudioDownloader.download` → `AudioDownloadResult`
4. `TranslateYouTubeVideo` calls `Transcriber.transcribe` → `TranscriptionResult`
5. The result is serialized and stored as two objects: a `Transcription` JSON and a `SentenceList` JSON
6. Router shapes the result into a `YouTubeTranslateResponse`
7. If `target_language` was requested, `TranslateTranscription` runs as a background task and writes a translated JSON blob

The ports/use cases live in `service.py` and depend only on the Protocols; concrete I/O (`client.py`) is injected by the router. Swap an adapter to test without hitting YouTube or OpenAI.

## Glossary

**VideoId** — The bare YouTube video identifier extracted from any supported URL form (e.g., `dQw4w9WgXcQ`). Used as the storage key prefix. Not the same as `VideoORM.id` in the Videos domain (they happen to share the same value, but the YouTube domain has no knowledge of the Videos domain).

**AudioDownloadResult** — What yt-dlp returns after a successful download: `video_id`, `title`, `audio_path` (local temp file), `duration_ms`, `source_url`.

**TranscriptionResult** — Output of one Whisper pass: detected `language`, full `text`, a list of `WordTimestamp`, and a list of `SpeakerSegment`.

**WordTimestamp** — A single transcribed word with `start` and `end` times in seconds.

**Sentence** — A contiguous run of words that form a natural sentence. Derived from a transcription by `build_sentences`; a Pydantic model in `schemas.py`, not stored in the domain data classes.

**Transcription** — The serialized JSON blob stored in object storage at `transcriptions/{video_id}.json`. Contains everything from `AudioDownloadResult` and `TranscriptionResult`. This is the cache unit — a hit on this key skips download and transcription entirely.

**SentenceList** — A second JSON blob stored at `transcriptions/{video_id}_sentences.json`, derived from the `Transcription` in the same use-case pass.

**AudioDownloader / Transcriber** (ports) — Protocols in `service.py` that `TranslateYouTubeVideo` depends on. Concrete implementations are `YtDlpAudioDownloader` and `WhisperTranscriber` in `client.py`.

## Flagged ambiguities

- **"translate" vs "transcribe"**: The route is `/youtube/translate` and the use case is `TranslateYouTubeVideo`, but Whisper's task here is transcription with English output (it both transcribes speech and maps it to English in one pass). Externally it is called "translate"; internally the data model calls the output `TranscriptionResult`. The code uses "transcription" everywhere except the HTTP surface — keep "translate" reserved for the route.

## Example dialogue

> **Dev**: Does `GetCachedTranscription` check the database?
>
> **Domain expert**: No — the YouTube domain has no database. A `Transcription` is a JSON file in object storage. The cache key is `transcriptions/{video_id}.json`. If that file exists, we return it; otherwise we run the full download-and-transcribe flow.
>
> **Dev**: What about the `Video` record in Postgres?
>
> **Domain expert**: That belongs to the Videos domain, which is separate. The YouTube domain doesn't know about it. When you ask the YouTube domain for a transcription you get back word timestamps; when you ask the Videos domain for a video you get back subtitle track metadata.
