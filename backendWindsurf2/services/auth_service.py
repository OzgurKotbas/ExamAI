"""
services/auth_service.py – Authentication service with Google OAuth integration.
"""

import logging
import random
import string
from typing import Tuple

import redis
from fastapi import Depends, Header, HTTPException, status
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User
from schemas.user import UserCreate
from services.email_service import send_password_reset_email
from utils.security import hash_password, verify_password, create_access_token, decode_access_token
from config import settings
from database import get_db

logger = logging.getLogger(__name__)

# Redis client for password reset codes
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def _log_auth_event(event_type: str, email: str, full_name: str = ""):
    """Log authentication events (register, login) to a file."""
    import os
    from datetime import datetime
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    log_file = os.path.join(log_dir, "auth_events.log")
    
    try:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        with open(log_file, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {event_type.upper()}: {email} | Name: {full_name}\n")
    except Exception as e:
        logger.error(f"Failed to log auth event: {str(e)}")


async def register_user(db: AsyncSession, user_data: UserCreate) -> User:
    """Register a new user with email & password."""
    try:
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == user_data.email))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Create new user
        hashed_password = hash_password(user_data.password)
        user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            is_active=True
        )
        
        db.add(user)
        await db.flush()   # ID üret; commit get_db dependency'de yapılır
        await db.refresh(user)
        
        _log_auth_event("REGISTER", user.email, user.full_name)
        logger.info(f"New user registered: {user.email}")
        return user
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        raise ValueError("Failed to register user")


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Tuple[User, str]:
    """Authenticate user with email & password and return user with token."""
    try:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("Invalid email or password")
        
        if not user.is_active:
            raise ValueError("User account is inactive")
        
        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")
        
        token = create_access_token(str(user.id))
        _log_auth_event("LOGIN", email, user.full_name)
        logger.info(f"User authenticated: {email}")
        return user, token
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error authenticating user: {str(e)}")
        raise ValueError("Authentication failed")


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> User:
    """Get current user from a Bearer token in the Authorization header."""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header. Expected 'Bearer <token>'.",
        )

    try:
        import uuid as _uuid

        user_id = decode_access_token(token)
        result = await db.execute(select(User).where(User.id == _uuid.UUID(user_id)))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or inactive token")

        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed to authenticate token")


def build_google_auth_url() -> str:
    """Build Google OAuth authorization URL."""
    try:
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise ValueError("Google OAuth credentials not configured")
        
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        auth_url = f"{base_url}?{query_string}"
        
        return auth_url
        
    except Exception as e:
        logger.error(f"Error building Google auth URL: {str(e)}")
        raise ValueError("Failed to build Google authentication URL")


async def google_login_or_create(db: AsyncSession, code: str) -> Tuple[User, str, bool]:
    """Handle Google OAuth callback and login or create user."""
    try:
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise ValueError("Google OAuth credentials not configured")
        
        # Exchange authorization code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            token_response.raise_for_status()
            token_info = token_response.json()
            access_token = token_info.get("access_token")
            
            if not access_token:
                raise ValueError("Failed to obtain access token from Google")
            
            # Get user info from Google
            user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            user_response = await client.get(user_info_url, headers=headers)
            user_response.raise_for_status()
            user_info = user_response.json()
            
            email = user_info.get("email")
            full_name = user_info.get("name", "")
            picture_url = user_info.get("picture", "")
            
            if not email:
                raise ValueError("Failed to get email from Google")
            
            # Check if user exists
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            is_new = False
            
            if user:
                # Existing user - update picture if changed
                if picture_url and user.picture_url != picture_url:
                    user.picture_url = picture_url
                
                # Check if active
                if not user.is_active:
                    logger.warning(f"Inactive user attempted Google OAuth login: {email}")
                    raise ValueError("User account is inactive")
                
                logger.info(f"Existing user logged in via Google OAuth: {email}")
            else:
                # Create new user
                is_new = True
                user = User(
                    email=email,
                    full_name=full_name,
                    picture_url=picture_url,
                    hashed_password="",  # No password for OAuth users
                    is_active=True,
                    is_google_auth=True,
                    is_oauth_user=True
                )
                
                db.add(user)
                await db.flush()   # ID üret; commit get_db dependency'de yapılır
                await db.refresh(user)
                
                logger.info(f"New user created via Google OAuth: {email}")
            
            # Create JWT token
            token = create_access_token(str(user.id))
            _log_auth_event("GOOGLE_LOGIN" if not is_new else "GOOGLE_REGISTER", email, full_name)
            return user, token, is_new

            
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error in Google OAuth: {str(e)}")
        raise ValueError("Failed to authenticate with Google")


# ─── Password Reset Functions ───────────────────────────────────────────────

def generate_reset_code() -> str:
    """Generate a 6-digit random reset code."""
    return ''.join(random.choices(string.digits, k=6))


def store_reset_code(email: str, code: str) -> bool:
    """Store reset code in Redis with expiration."""
    try:
        key = f"password_reset:{email}"
        redis_client.setex(key, settings.RESET_CODE_EXPIRE_MINUTES * 60, code)
        return True
    except Exception as e:
        logger.error(f"Error storing reset code: {str(e)}")
        return False


def verify_reset_code(email: str, code: str) -> bool:
    """Verify reset code from Redis."""
    try:
        key = f"password_reset:{email}"
        stored_code = redis_client.get(key)
        if stored_code and stored_code == code:
            return True
        return False
    except Exception as e:
        logger.error(f"Error verifying reset code: {str(e)}")
        return False


def delete_reset_code(email: str) -> bool:
    """Delete reset code from Redis."""
    try:
        key = f"password_reset:{email}"
        redis_client.delete(key)
        return True
    except Exception as e:
        logger.error(f"Error deleting reset code: {str(e)}")
        return False


async def request_password_reset(db: AsyncSession, email: str) -> Tuple[bool, str]:
    """Request password reset - generates code and sends email."""
    try:
        # Check if user exists
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            # Don't reveal if user exists or not for security
            logger.info(f"Password reset requested for non-existent email: {email}")
            return True, "If the email exists, a reset code has been sent"
        
        # Don't allow password reset for OAuth-only users
        if user.is_oauth_user and not user.hashed_password:
            logger.warning(f"Password reset attempted for OAuth-only user: {email}")
            return True, "If the email exists, a reset code has been sent"
        
        # Generate and store reset code
        reset_code = generate_reset_code()
        if not store_reset_code(email, reset_code):
            raise ValueError("Failed to store reset code")
        
        # Send email
        email_sent = send_password_reset_email(email, reset_code, user.full_name)
        if not email_sent:
            delete_reset_code(email)
            logger.error(
                f"Password reset email could not be sent to {email}. "
                "Please verify SMTP_USER, SMTP_PASSWORD, SMTP_HOST and SMTP_PORT in the .env file."
            )
            raise ValueError(
                "Şifre sıfırlama e-postası gönderilemedi. "
                "Lütfen sistem yöneticisiyle iletişime geçin veya daha sonra tekrar deneyin."
            )
        
        logger.info(f"Password reset code sent to: {email}")
        return True, "Reset code sent to your email"
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error requesting password reset: {str(e)}")
        raise ValueError("Failed to process password reset request")


async def reset_password(db: AsyncSession, email: str, code: str, new_password: str) -> Tuple[bool, str]:
    """Reset password with verification code."""
    try:
        # Verify the reset code
        if not verify_reset_code(email, code):
            raise ValueError("Invalid or expired reset code")
        
        # Get user
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        # Update password
        user.hashed_password = hash_password(new_password)
        await db.flush()
        await db.refresh(user)
        
        # Delete the used reset code
        delete_reset_code(email)
        
        logger.info(f"Password reset successful for: {email}")
        return True, "Password reset successfully"
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        raise ValueError("Failed to reset password")


# ─── Profile Update Functions ───────────────────────────────────────────────

async def update_user_profile(db: AsyncSession, user: User, full_name: str, email: str) -> User:
    """Update user profile (name and email)."""
    try:
        # Check if email is being changed and if it's already taken
        if email != user.email:
            result = await db.execute(select(User).where(User.email == email))
            existing_user = result.scalar_one_or_none()
            if existing_user:
                raise ValueError("Email address is already in use")
        
        # Update user
        user.full_name = full_name
        user.email = email
        await db.flush()
        await db.refresh(user)
        
        logger.info(f"User profile updated: {user.email}")
        return user
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        raise ValueError("Failed to update profile")


async def change_user_password(db: AsyncSession, user: User, current_password: str, new_password: str) -> bool:
    """Change password for logged-in user."""
    try:
        # Verify current password
        if not user.hashed_password or not verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")
        
        # Update password
        user.hashed_password = hash_password(new_password)
        await db.flush()
        await db.refresh(user)
        
        logger.info(f"Password changed for user: {user.email}")
        return True
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        raise ValueError("Failed to change password")
