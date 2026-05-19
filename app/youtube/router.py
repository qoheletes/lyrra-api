import tempfile

from fastapi import APIRouter, HTTPException
from yt_dlp.utils import DownloadError

from app.youtube.schemas import SentencesResponse, YouTubeTranslateRequest, YouTubeTranslateResponse
from app.youtube.sentences import build_sentences
from app.youtube.service import (
    build_translate_response,
    download_youtube_audio,
    get_cached_transcription,
    normalize_youtube_video_id,
    save_sentences,
    save_transcription,
    translate_audio,
)

router = APIRouter(tags=["youtube"])


@router.get("/youtube/transcribe/{video_id}/sentences", response_model=SentencesResponse)
def get_sentences(video_id: str) -> SentencesResponse:
    transcription = get_cached_transcription(video_id)
    if transcription is None:
        raise HTTPException(status_code=404, detail=f"No cached transcription for video_id={video_id!r}")
    return SentencesResponse(
        video_id=video_id,
        language=transcription.get("language"),
        sentences=build_sentences(transcription),
    )


@router.post("/youtube/translate", response_model=YouTubeTranslateResponse)
def translate_youtube_video(
    request: YouTubeTranslateRequest,
) -> YouTubeTranslateResponse:
    video_id = normalize_youtube_video_id(str(request.youtube_url))
    if video_id:
        cached = get_cached_transcription(video_id)
        if cached:
            return build_translate_response(cached, request.include_words)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            video_data = download_youtube_audio(str(request.youtube_url), temp_dir)
            result = translate_audio(
                audio_path=video_data["audio_path"],
                model_name=request.model,
                source_language=request.source_language,
            )
            print(
                f"[translate] language={result['language']!r}"
                f" words={len(result['words'])}"
                f"\n{result['text']}"
            )
    except DownloadError as exc:
        raise HTTPException(
            status_code=400, detail=f"YouTube download failed: {exc}"
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail="ffmpeg is required by yt-dlp/Whisper but was not found on the server.",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=f"Whisper failed: {exc}") from exc

    save_transcription(video_data, result)
    video_id = video_data["video_id"]
    save_sentences(video_id, result)
    data = {
        "video_id": video_data["video_id"],
        "title": video_data["title"],
        "duration_ms": video_data.get("duration_ms"),
        "language": result.get("language"),
        "text": result.get("text", ""),
        "words": result.get("words", []),
    }
    return build_translate_response(data, request.include_words)
