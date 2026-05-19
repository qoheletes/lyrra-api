# makeaudio

FastAPI server that accepts a YouTube URL, checks whether a translated result already exists in the database, and otherwise downloads the audio, translates the speech to English with Whisper, stores the result, and returns it.

## Requirements

- Python 3.9+
- `ffmpeg` installed and available on `PATH`

On macOS with Homebrew:

```bash
brew install ffmpeg
```

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

## API

`POST /youtube/translate`

Behavior:

1. Normalize the incoming YouTube URL and search the `videos` table for an existing translated result.
2. If found, return the stored translation directly from the database.
3. If not found, download the audio, run Whisper translation, store the translated text and segments in the database, and return the new result.

Example request:

```bash
curl -X POST http://127.0.0.1:8000/youtube/translate \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "model": "base",
    "source_language": null,
    "include_segments": true
  }'
```

Example response:

```json
{
  "title": "Video title",
  "video_id": "abc123",
  "source_language": "ko",
  "translated_text": "Translated English text",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 3.2,
      "text": "Translated segment"
    }
  ]
}
```

## Notes

- Whisper will download the selected model the first time you use it.
- `task="translate"` translates speech into English.
- Some YouTube videos may block download or require additional cookies/authentication.
