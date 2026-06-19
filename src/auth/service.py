from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.exc import IntegrityError

from src.auth.exceptions import EmailAlreadyExists, InvalidCredentials
from src.auth.models import UserORM
from src.auth.security import hash_password, verify_password

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def create_user(db: Session, email: str, password: str) -> UserORM:
    if db.query(UserORM.id).filter(UserORM.email == email).scalar() is not None:
        raise EmailAlreadyExists(email)
    user = UserORM(email=email, password_hash=hash_password(password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise EmailAlreadyExists(email) from exc
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> UserORM:
    user = db.query(UserORM).filter(UserORM.email == email).first()
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentials()
    return user


def get_user_by_id(db: Session, user_id: int) -> UserORM | None:
    return db.query(UserORM).filter(UserORM.id == user_id).first()
