"""
routers/auth.py – Authentication endpoints.
"""

import logging
from fastapi import APIRouter, Depends, Form, status, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from schemas.user import TokenResponse, UserCreate, UserRead, ErrorResponse
from services.auth_service import (
    authenticate_user,
    build_google_auth_url,
    get_current_user,
    google_login_or_create,
    register_user,
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


@router.get("/google/callback", response_model=TokenResponse)
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Handle Google OAuth callback and issue JWT."""
    try:
        if not code:
            raise ValueError("Authorization code is required")
        
        user, token = await google_login_or_create(db, code)
        logger.info(f"Google OAuth successful for user: {user.email}")
        return {"access_token": token, "user": user}
    except ValueError as e:
        logger.warning(f"Google OAuth callback failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during Google OAuth callback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during Google authentication"
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
