from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.auth import service
from src.auth.exceptions import InvalidToken
from src.auth.models import UserORM
from src.auth.security import decode_token
from src.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

DbDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


def get_current_user(token: TokenDep, db: DbDep) -> UserORM:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
    except InvalidToken as exc:
        raise credentials_exception from exc

    subject = payload.get("sub")
    if subject is None:
        raise credentials_exception
    try:
        user_id = int(subject)
    except (TypeError, ValueError) as exc:
        raise credentials_exception from exc

    user = service.get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    return user


CurrentUserDep = Annotated[UserORM, Depends(get_current_user)]
