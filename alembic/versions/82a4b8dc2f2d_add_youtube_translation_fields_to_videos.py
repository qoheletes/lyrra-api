"""add youtube translation fields to videos

Revision ID: 82a4b8dc2f2d
Revises: 22961aac149a
Create Date: 2026-04-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "82a4b8dc2f2d"
down_revision: Union[str, None] = "22961aac149a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("videos", sa.Column("youtube_url", sa.String(length=500), nullable=True))
    op.add_column("videos", sa.Column("translated_text", sa.Text(), nullable=True))
    op.add_column(
        "videos",
        sa.Column("translated_segments", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column("videos", sa.Column("translated_language", sa.String(length=5), nullable=True))
    op.create_index("ix_videos_youtube_video_id", "videos", ["youtube_video_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_videos_youtube_video_id", table_name="videos")
    op.drop_column("videos", "translated_language")
    op.drop_column("videos", "translated_segments")
    op.drop_column("videos", "translated_text")
    op.drop_column("videos", "youtube_video_id")
    op.drop_column("videos", "youtube_url")
