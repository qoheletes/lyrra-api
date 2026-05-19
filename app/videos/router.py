from fastapi import APIRouter, Depends

from app.videos.dependencies import get_video_or_404
from app.videos.models import Video
from app.videos.schemas import VideoOut

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("/{video_id}", response_model=VideoOut)
def get_video(video: Video = Depends(get_video_or_404)) -> VideoOut:
    return VideoOut.model_validate(video)
