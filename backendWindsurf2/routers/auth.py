"""
routers/auth.py – Authentication endpoints.
"""

import logging
import urllib.parse
from fastapi import APIRouter, Depends, Form, status, HTTPException, Header
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models.user import User
from schemas.user import TokenResponse, UserCreate, UserRead, ErrorResponse, PasswordResetRequest, PasswordResetVerify, PasswordResetResponse
from services.auth_service import (
    authenticate_user,
    build_google_auth_url,
    get_current_user,
    google_login_or_create,
    register_user,
    request_password_reset,
    reset_password,
    update_user_profile,
    change_user_password,
)
from services.ai_service import validate_gemini_api_key, SUPPORTED_GEMINI_MODELS
from utils.security import create_access_token
from utils.i18n import translate


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/gemini-models")
async def get_gemini_models():
    """Return the list of supported Gemini models for the frontend dropdown."""
    return {"models": SUPPORTED_GEMINI_MODELS}


@router.post("/validate-gemini-key")
async def validate_gemini_key(
    gemini_api_key: str = Form(...),
    gemini_model: str = Form(...),
    current_user: User = Depends(get_current_user),
    lang: str = Header("tr", alias="X-Language"),
):
    """
    Validate user's Gemini API key + model by sending a 1-token test request.
    Returns JSON: { valid: bool, message: str }
    """
    result = await validate_gemini_api_key(gemini_api_key, gemini_model, lang)
    message = translate(result["message_key"], lang)
    return {"valid": result["valid"], "message": message}

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: UserCreate, 
    db: AsyncSession = Depends(get_db),
    lang: str = Header("tr", alias="X-Language")
):
    """Register a new user with email & password."""
    try:
        user = await register_user(db, body, lang=lang)
        token = create_access_token(str(user.id))
        logger.info(f"User registered successfully: {user.email}")
        return {"access_token": token, "user": user}
    except ValueError as e:
        logger.warning(f"Registration failed for {body.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during registration for {body.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=translate("REGISTRATION_FAILED", lang)
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    email: str = Form(...), 
    password: str = Form(...), 
    db: AsyncSession = Depends(get_db),
    lang: str = Header("tr", alias="X-Language")
):
    """Login with email & password (form body)."""
    try:
        user, token = await authenticate_user(db, email, password, lang=lang)
        logger.info(f"User logged in successfully: {email}")
        return {"access_token": token, "user": user}
    except ValueError as e:
        logger.warning(f"Login failed for {email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during login for {email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=translate("LOGIN_FAILED", lang)
        )


@router.get("/google")
async def google_login(lang: str = Header("tr", alias="X-Language")):
    """Redirect user to Google OAuth consent screen."""
    try:
        auth_url = build_google_auth_url()
        logger.info("Google OAuth URL generated successfully")
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"Failed to generate Google OAuth URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=translate("INTERNAL_SERVER_ERROR", lang)
        )


@router.get("/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Handle Google OAuth callback and redirect to frontend with token."""
    try:
        if not code:
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error=Yetkilendirme kodu eksik",
                status_code=302
            )
        
        user, token, is_new = await google_login_or_create(db, code)
        logger.info(f"Google OAuth successful for user: {user.email} (is_new: {is_new})")
        
        # Redirect to frontend with token and user info as query params
        redirect_url = f"{settings.FRONTEND_URL}/auth/callback?token={token}&user_id={user.id}&email={urllib.parse.quote(user.email)}&name={urllib.parse.quote(user.full_name or '')}&is_new={str(is_new).lower()}"
        
        return RedirectResponse(url=redirect_url, status_code=302)

        
    except ValueError as e:
        logger.warning(f"Google OAuth callback failed: {str(e)}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error={urllib.parse.quote(str(e))}",
            status_code=302
        )
    except Exception as e:
        logger.error(f"Unexpected error during Google OAuth callback: {str(e)}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=Kimlik doğrulama başarısız oldu",
            status_code=302
        )


@router.get("/me", response_model=UserRead)
async def me(
    current_user: User = Depends(get_current_user),
    lang: str = Header("tr", alias="X-Language")
):
    """Returns the current authenticated user's profile (Bearer token required)."""
    try:
        logger.info(f"Profile retrieved for user: {current_user.email}")
        return current_user
    except Exception as e:
        logger.error(f"Error retrieving user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=translate("INTERNAL_SERVER_ERROR", lang)
        )


@router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(
    body: PasswordResetRequest, 
    db: AsyncSession = Depends(get_db),
    lang: str = Header("tr", alias="X-Language")
):
    """Request password reset - sends reset code to email."""
    try:
        success, message = await request_password_reset(db, body.email, lang=lang)
        return {"success": success, "message": message}
    except ValueError as e:
        logger.warning(f"Password reset request failed for {body.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during password reset request for {body.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=translate("INTERNAL_SERVER_ERROR", lang)
        )


@router.post("/reset-password", response_model=PasswordResetResponse)
async def reset_password_endpoint(
    body: PasswordResetVerify, 
    db: AsyncSession = Depends(get_db),
    lang: str = Header("tr", alias="X-Language")
):
    """Reset password with verification code."""
    try:
        success, message = await reset_password(db, body.email, body.code, body.new_password, lang=lang)
        return {"success": success, "message": message}
    except ValueError as e:
        logger.warning(f"Password reset failed for {body.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during password reset for {body.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=translate("INTERNAL_SERVER_ERROR", lang)
        )


@router.put("/profile", response_model=UserRead)
async def update_profile(
    full_name: str = Form(...),
    email: str = Form(...),
    gemini_api_key: str | None = Form(None),
    gemini_model: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lang: str = Header("tr", alias="X-Language")
):
    """Update current user's profile (name, email, API key and preferred model)."""
    try:
        updated_user = await update_user_profile(db, current_user, full_name, email, gemini_api_key, gemini_model, lang=lang)
        logger.info(f"Profile updated for user: {updated_user.email}")
        return updated_user
    except ValueError as e:
        logger.warning(f"Profile update failed for {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during profile update for {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=translate("PROFILE_UPDATE_FAILED", lang)
        )


@router.post("/change-password", response_model=PasswordResetResponse)
async def change_password(
    current_password: str = Form(...),
    new_password: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lang: str = Header("tr", alias="X-Language")
):
    """Change password for logged-in user."""
    try:
        success = await change_user_password(db, current_user, current_password, new_password, lang=lang)
        logger.info(f"Password changed for user: {current_user.email}")
        return {"success": success, "message": translate("PASSWORD_CHANGE_SUCCESS", lang)}
    except ValueError as e:
        logger.warning(f"Password change failed for {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during password change for {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=translate("PASSWORD_CHANGE_FAILED", lang)
        )
