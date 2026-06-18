from __future__ import annotations

from datetime import datetime  # noqa: TC003 — resolved at runtime by SQLAlchemy's Mapped[]

from sqlalchemy import BigInteger, DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base

# BigInteger on Postgres; INTEGER on SQLite so the autoincrement PK works in tests.
BigIntPK = BigInteger().with_variant(Integer, "sqlite")


class UserORM(Base):
    __tablename__ = "user"
    __table_args__ = (Index("ix_user_email", "email", unique=True),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
