"""
routers/auth.py – Authentication endpoints.
"""

import logging
import urllib.parse
from fastapi import APIRouter, Depends, Form, status, HTTPException
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
from utils.security import create_access_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user with email & password."""
    try:
        user = await register_user(db, body)
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
            detail="Internal server error during registration"
        )


@router.post("/login", response_model=TokenResponse)
async def login(email: str = Form(...), password: str = Form(...), db: AsyncSession = Depends(get_db)):
    """Login with email & password (form body)."""
    try:
        user, token = await authenticate_user(db, email, password)
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
            detail="Internal server error during login"
        )


@router.get("/google")
async def google_login():
    """Redirect user to Google OAuth consent screen."""
    try:
        auth_url = build_google_auth_url()
        logger.info("Google OAuth URL generated successfully")
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"Failed to generate Google OAuth URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Google OAuth URL"
        )


@router.get("/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Handle Google OAuth callback and redirect to frontend with token."""
    try:
        if not code:
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error=Authorization code is required",
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
            url=f"{settings.FRONTEND_URL}/login?error=Authentication failed",
            status_code=302
        )


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)):
    """Returns the current authenticated user's profile (Bearer token required)."""
    try:
        logger.info(f"Profile retrieved for user: {current_user.email}")
        return current_user
    except Exception as e:
        logger.error(f"Error retrieving user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(body: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    """Request password reset - sends reset code to email."""
    try:
        success, message = await request_password_reset(db, body.email)
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
            detail="Failed to process password reset request"
        )


@router.post("/reset-password", response_model=PasswordResetResponse)
async def reset_password_endpoint(body: PasswordResetVerify, db: AsyncSession = Depends(get_db)):
    """Reset password with verification code."""
    try:
        success, message = await reset_password(db, body.email, body.code, body.new_password)
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
            detail="Failed to reset password"
        )


@router.put("/profile", response_model=UserRead)
async def update_profile(
    full_name: str = Form(...),
    email: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile (name and email)."""
    try:
        updated_user = await update_user_profile(db, current_user, full_name, email)
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
            detail="Failed to update profile"
        )


@router.post("/change-password", response_model=PasswordResetResponse)
async def change_password(
    current_password: str = Form(...),
    new_password: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change password for logged-in user."""
    try:
        success = await change_user_password(db, current_user, current_password, new_password)
        logger.info(f"Password changed for user: {current_user.email}")
        return {"success": success, "message": "Password changed successfully"}
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
            detail="Failed to change password"
        )
