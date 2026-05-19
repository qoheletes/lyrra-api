from sqlalchemy.orm import Session, selectinload

from app.videos.exceptions import VideoNotFound
from app.videos.models import Video


def get_video_with_tracks(video_id: int, db: Session) -> Video:
    video = (
        db.query(Video)
        .options(selectinload(Video.subtitle_tracks))
        .filter(Video.id == video_id)
        .first()
    )
    if video is None:
        raise VideoNotFound(video_id)
    return video
