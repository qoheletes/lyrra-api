from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# bcrypt rejects inputs longer than 72 bytes, so cap the password there: a longer
# value would otherwise reach bcrypt and raise instead of failing validation cleanly.
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
