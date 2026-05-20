from fastapi import APIRouter, Depends, Form, HTTPException, Response, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage.client import StorageAdapter, get_storage
from app.subtitles.application.use_cases import DeleteSubtitle, GetSubtitleTrackUrl, UploadSubtitle
from app.subtitles.domain.exceptions import InvalidSubtitleJSONError, TrackNotFoundError
from app.subtitles.infrastructure.repository import SubtitleRepository
from app.subtitles.infrastructure.schemas import SubtitleTrackOut
from app.videos.domain.exceptions import VideoNotFoundError
from app.videos.infrastructure.repository import VideoRepository

router = APIRouter(prefix="/videos/{video_id}/subtitles", tags=["subtitles"])


def _get_upload_uc(
    db: Session = Depends(get_db),
    storage: StorageAdapter = Depends(get_storage),
) -> UploadSubtitle:
    return UploadSubtitle(SubtitleRepository(db), VideoRepository(db), storage)


def _get_delete_uc(
    db: Session = Depends(get_db),
    storage: StorageAdapter = Depends(get_storage),
) -> DeleteSubtitle:
    return DeleteSubtitle(SubtitleRepository(db), storage)


def _get_track_url_uc(db: Session = Depends(get_db)) -> GetSubtitleTrackUrl:
    return GetSubtitleTrackUrl(SubtitleRepository(db))


@router.post("", response_model=SubtitleTrackOut, status_code=200)
async def upload_subtitle_track(
    video_id: str,
    file: UploadFile,
    language_code: str = Form(...),
    format: str = Form("json"),
    uc: UploadSubtitle = Depends(_get_upload_uc),
) -> SubtitleTrackOut:
    file_bytes = await file.read()
    try:
        track = uc.execute(video_id, language_code, format, file_bytes)
    except VideoNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidSubtitleJSONError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SubtitleTrackOut.model_validate(track)


@router.delete("/{language_code}", status_code=204)
def delete_subtitle_track(
    video_id: str,
    language_code: str,
    uc: DeleteSubtitle = Depends(_get_delete_uc),
) -> Response:
    try:
        uc.execute(video_id, language_code)
    except TrackNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=204)


@router.get("/{language_code}", status_code=302)
def get_subtitle_track(
    video_id: str,
    language_code: str,
    uc: GetSubtitleTrackUrl = Depends(_get_track_url_uc),
) -> RedirectResponse:
    try:
        url = uc.execute(video_id, language_code)
    except TrackNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RedirectResponse(url=url, status_code=302)
