from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.auth import service
from src.auth.dependencies import CurrentUserDep
from src.auth.exceptions import EmailAlreadyExists, InvalidCredentials
from src.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from src.auth.security import create_access_token
from src.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

DbDep = Annotated[Session, Depends(get_db)]


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbDep) -> UserOut:
    try:
        user = service.create_user(db, payload.email, payload.password)
    except EmailAlreadyExists as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return UserOut.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbDep) -> TokenResponse:
    try:
        user = service.authenticate(db, payload.email, payload.password)
    except InvalidCredentials as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
def me(current_user: CurrentUserDep) -> UserOut:
    return UserOut.model_validate(current_user)
