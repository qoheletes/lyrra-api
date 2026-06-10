import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.database import Base, engine
from src.subtitles.models import SubtitleTrackORM  # noqa: F401 — registers model with Base
from src.subtitles.router import router as subtitles_router
from src.videos.models import VideoORM  # noqa: F401 — registers model with Base
from src.videos.router import router as videos_router
from src.youtube.router import router as youtube_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("lyrra")


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

@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
