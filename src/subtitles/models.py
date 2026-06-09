from __future__ import annotations

from datetime import datetime  # noqa: TC003 — resolved at runtime by SQLAlchemy's Mapped[]
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.videos.models import VideoORM


class SubtitleTrackORM(Base):
    __tablename__ = "subtitle_tracks"
    __table_args__ = (
        UniqueConstraint("video_id", "language_code", name="uq_subtitle_tracks_video_lang"),
        Index("ix_subtitle_tracks_video_id", "video_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    video_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False
    )
    language_code: Mapped[str] = mapped_column(String(5), nullable=False)
    format: Mapped[str] = mapped_column(String(10), nullable=False, default="json")
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_machine_translated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="published")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    video: Mapped[VideoORM] = relationship("VideoORM", back_populates="subtitle_tracks")
