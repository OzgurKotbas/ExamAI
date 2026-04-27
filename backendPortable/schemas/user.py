"""
schemas/user.py – Pydantic schemas for the User resource.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    password: str


class UserCreateGoogle(UserBase):
    picture_url: str | None = None


class UserRead(UserBase):
    id: uuid.UUID
    picture_url: str | None
    is_active: bool
    is_google_auth: bool
    is_oauth_user: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class GoogleCallbackRequest(BaseModel):
    code: str
    state: str | None = None


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None
