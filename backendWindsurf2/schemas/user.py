"""
schemas/user.py – Pydantic schemas for the User resource.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    gemini_model: str | None = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    gemini_model: str | None = None


class UserCreateGoogle(UserBase):
    picture_url: str | None = None


class UserRead(UserBase):
    id: uuid.UUID
    picture_url: str | None
    is_active: bool
    is_google_auth: bool
    is_oauth_user: bool
    # Raw DB value (encrypted or legacy plaintext) — never sent to client as-is.
    # The validator below replaces it with a masked version (e.g. "****abcd").
    gemini_api_key: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("gemini_api_key", mode="before")
    @classmethod
    def mask_api_key(cls, v: str | None) -> str | None:
        """Mask the stored key before returning it to the frontend.

        The actual plaintext key must never leave the backend. We decrypt the
        stored key first, and then expose only the last 4 characters of the
        actual key so the user can recognize which key is saved, prefixed with '****'.
        """
        if not v:
            return None
        
        from utils.security import safe_decrypt_api_key
        decrypted = safe_decrypt_api_key(v)
        if not decrypted:
            return None
            
        visible = decrypted[-4:] if len(decrypted) >= 4 else decrypted
        return f"****{visible}"


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


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetVerify(BaseModel):
    email: EmailStr
    code: str
    new_password: str


class PasswordResetResponse(BaseModel):
    message: str
    success: bool


class MessageResponse(BaseModel):
    message: str
