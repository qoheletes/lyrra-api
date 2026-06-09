from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Response, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from src.database import get_db
from src.storage.client import StorageAdapter, get_storage
from src.subtitles import service
from src.subtitles.exceptions import InvalidSubtitleJSONError, TrackNotFoundError
from src.subtitles.schemas import SubtitleTrackOut
from src.videos.exceptions import VideoNotFoundError

router = APIRouter(prefix="/videos/{video_id}/subtitles", tags=["subtitles"])

DbDep = Annotated[Session, Depends(get_db)]
StorageDep = Annotated[StorageAdapter, Depends(get_storage)]


@router.post("", response_model=SubtitleTrackOut, status_code=200)
async def upload_subtitle_track(
    video_id: str,
    file: UploadFile,
    db: DbDep,
    storage: StorageDep,
    language_code: str = Form(...),
    format: str = Form("json"),
) -> SubtitleTrackOut:
    file_bytes = await file.read()
    try:
        track = service.upload_subtitle(db, storage, video_id, language_code, format, file_bytes)
    except VideoNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidSubtitleJSONError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SubtitleTrackOut.model_validate(track)


@router.delete("/{language_code}", status_code=204)
def delete_subtitle_track(
    video_id: str,
    language_code: str,
    db: DbDep,
    storage: StorageDep,
) -> Response:
    try:
        service.delete_subtitle(db, storage, video_id, language_code)
    except TrackNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=204)


@router.get("/{language_code}", status_code=302)
def get_subtitle_track(
    video_id: str,
    language_code: str,
    db: DbDep,
) -> RedirectResponse:
    try:
        url = service.get_track_url(db, video_id, language_code)
    except TrackNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RedirectResponse(url=url, status_code=302)
