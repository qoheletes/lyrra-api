import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("lyrra")

from app.core.config import settings
from app.core.database import Base, engine
from app.subtitles.infrastructure.orm_models import SubtitleTrackORM  # noqa: F401 — registers model with Base
from app.videos.infrastructure.orm_models import VideoORM  # noqa: F401 — registers model with Base
from app.subtitles.infrastructure.router import router as subtitles_router
from app.videos.infrastructure.router import router as videos_router
from app.youtube.infrastructure.router import router as youtube_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Lyrra API",
    version="0.2.0",
    description="YouTube audio translation and video subtitle management.",
    lifespan=lifespan,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    logger.info("→ %s %s", request.method, request.url.path)
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    logger.info(
        "← %s %s %d %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(videos_router)
app.include_router(subtitles_router)
app.include_router(youtube_router)

if settings.storage_backend == "local":
    os.makedirs(settings.local_storage_path, exist_ok=True)
    app.mount(
        "/files", StaticFiles(directory=settings.local_storage_path), name="files"
    )


@app.get("/health")
def healthcheck() -> Dict[str, str]:
    return {"status": "ok"}
