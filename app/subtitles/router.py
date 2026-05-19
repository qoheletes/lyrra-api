from fastapi import APIRouter, Depends, Form, Response, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.storage.client import StorageAdapter, get_storage
from app.subtitles.exceptions import TrackNotFound
from app.subtitles.models import SubtitleTrack
from app.subtitles.schemas import SubtitleTrackOut
from app.subtitles.service import delete_subtitle, upload_subtitle

router = APIRouter(prefix="/videos/{video_id}/subtitles", tags=["subtitles"])


@router.post("", response_model=SubtitleTrackOut, status_code=200)
async def upload_subtitle_track(
    video_id: int,
    file: UploadFile,
    language_code: str = Form(...),
    format: str = Form("json"),
    db: Session = Depends(get_db),
    storage: StorageAdapter = Depends(get_storage),
) -> SubtitleTrackOut:
    file_bytes = await file.read()
    track = upload_subtitle(video_id, language_code, format, file_bytes, db, storage)
    return SubtitleTrackOut.model_validate(track)


@router.delete("/{language_code}", status_code=204)
def delete_subtitle_track(
    video_id: int,
    language_code: str,
    db: Session = Depends(get_db),
    storage: StorageAdapter = Depends(get_storage),
) -> Response:
    delete_subtitle(video_id, language_code, db, storage)
    return Response(status_code=204)


@router.get("/{language_code}", status_code=302)
def get_subtitle_track(
    video_id: int,
    language_code: str,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    track = (
        db.query(SubtitleTrack)
        .filter(
            SubtitleTrack.video_id == video_id,
            SubtitleTrack.language_code == language_code,
        )
        .first()
    )
    if track is None:
        raise TrackNotFound(video_id, language_code)
    return RedirectResponse(url=track.file_url, status_code=302)
