"""
services/auth_service.py – Authentication service with Google OAuth integration.
"""

import logging
from typing import Tuple

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User
from schemas.user import UserCreate
from utils.security import hash_password, verify_password, create_access_token, decode_access_token
from config import settings

logger = logging.getLogger(__name__)


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
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"New user registered: {user.email}")
        return user
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        await db.rollback()
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
        logger.info(f"User authenticated: {email}")
        return user, token
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error authenticating user: {str(e)}")
        raise ValueError("Authentication failed")


async def get_current_user(db: AsyncSession, token: str) -> User:
    """Get current user from JWT token."""
    try:
        import uuid as _uuid
        
        user_id = decode_access_token(token)
        result = await db.execute(select(User).where(User.id == _uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        if not user.is_active:
            raise ValueError("User account is inactive")
        
        return user
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise ValueError("Failed to authenticate token")


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


async def google_login_or_create(db: AsyncSession, code: str) -> Tuple[User, str]:
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
            
            if not email:
                raise ValueError("Failed to get email from Google")
            
            # Check if user exists
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            
            if user:
                # Existing user - check if active
                if not user.is_active:
                    logger.warning(f"Inactive user attempted Google OAuth login: {email}")
                    raise ValueError("User account is inactive")
                
                logger.info(f"Existing user logged in via Google OAuth: {email}")
            else:
                # Create new user
                user = User(
                    email=email,
                    full_name=full_name,
                    hashed_password="",  # No password for OAuth users
                    is_active=True,
                    is_google_auth=True,
                    is_oauth_user=True
                )
                
                db.add(user)
                await db.commit()
                await db.refresh(user)
                
                logger.info(f"New user created via Google OAuth: {email}")
            
            # Create JWT token
            token = create_access_token(str(user.id))
            return user, token
            
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error in Google OAuth: {str(e)}")
        await db.rollback()
        raise ValueError("Failed to authenticate with Google")
