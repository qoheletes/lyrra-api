from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db
from src.videos import service
from src.videos.exceptions import VideoNotFoundError
from src.videos.schemas import VideoOut

router = APIRouter(prefix="/videos", tags=["videos"])

DbDep = Annotated[Session, Depends(get_db)]


@router.get("/{video_id}", response_model=VideoOut)
def get_video(video_id: str, db: DbDep) -> VideoOut:
    try:
        video = service.get_with_tracks(db, video_id)
    except VideoNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return VideoOut.model_validate(video)
