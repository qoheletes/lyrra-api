"""create_videos_and_subtitle_tracks

Revision ID: 22961aac149a
Revises:
Create Date: 2026-04-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "22961aac149a"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "videos",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("default_lang", sa.String(5), nullable=False, server_default="en"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "subtitle_tracks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("video_id", sa.BigInteger(), nullable=False),
        sa.Column("language_code", sa.String(5), nullable=False),
        sa.Column("format", sa.String(10), nullable=False, server_default="vtt"),
        sa.Column("file_url", sa.String(500), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("is_machine_translated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(20), nullable=False, server_default="published"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("video_id", "language_code", name="uq_subtitle_tracks_video_lang"),
    )
    op.create_index("ix_subtitle_tracks_video_id", "subtitle_tracks", ["video_id"])


def downgrade() -> None:
    op.drop_index("ix_subtitle_tracks_video_id", table_name="subtitle_tracks")
    op.drop_table("subtitle_tracks")
    op.drop_table("videos")
