from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.videos.models import Video
from app.videos.service import get_video_with_tracks


def get_video_or_404(video_id: int, db: Session = Depends(get_db)) -> Video:
    return get_video_with_tracks(video_id, db)
