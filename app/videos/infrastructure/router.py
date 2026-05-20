from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.videos.application.use_cases import GetVideoWithTracks
from app.videos.domain.exceptions import VideoNotFoundError
from app.videos.infrastructure.repository import VideoRepository
from app.videos.infrastructure.schemas import SubtitleTrackOut, VideoOut

router = APIRouter(prefix="/videos", tags=["videos"])


def _get_use_case(db: Session = Depends(get_db)) -> GetVideoWithTracks:
    return GetVideoWithTracks(VideoRepository(db))


@router.get("/{video_id}", response_model=VideoOut)
def get_video(
    video_id: str,
    uc: GetVideoWithTracks = Depends(_get_use_case),
) -> VideoOut:
    try:
        video = uc.execute(video_id)
    except VideoNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return VideoOut(
        id=video.id,
        title=video.title,
        duration_ms=video.duration_ms,
        source_url=video.source_url,
        default_lang=video.default_lang,
        created_at=video.created_at,
        updated_at=video.updated_at,
        subtitle_tracks=[
            SubtitleTrackOut(
                language_code=t.language_code,
                file_url=t.file_url,
                format=t.format,
            )
            for t in video.subtitle_tracks
        ],
    )
