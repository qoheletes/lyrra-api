from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.subtitles.models import SubtitleTrack


class Video(Base):
    __tablename__ = "videos"
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    default_lang: Mapped[str] = mapped_column(String(5), nullable=False, default="en")
    translated_segments: Mapped[Optional[list[dict]]] = mapped_column(
        JSONB, nullable=True
    )
    translated_language: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    translated_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    subtitle_tracks: Mapped[List[SubtitleTrack]] = relationship(
        "SubtitleTrack", back_populates="video", cascade="all, delete-orphan"
    )
