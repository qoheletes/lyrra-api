from __future__ import annotations

from datetime import datetime  # noqa: TC003 — resolved at runtime by SQLAlchemy's Mapped[]
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.subtitles.models import SubtitleTrackORM


class VideoORM(Base):
    __tablename__ = "videos"
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    default_lang: Mapped[str] = mapped_column(String(5), nullable=False, default="en")
    translated_segments: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    translated_language: Mapped[str | None] = mapped_column(String(5), nullable=True)
    translated_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    subtitle_tracks: Mapped[list[SubtitleTrackORM]] = relationship(
        "SubtitleTrackORM", back_populates="video", cascade="all, delete-orphan"
    )
