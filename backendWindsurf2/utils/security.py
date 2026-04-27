"""
utils/security.py – JWT creation/verification and AES-256-GCM note encryption.
"""

import base64
import logging
import os
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import JWTError, jwt
from passlib.context import CryptContext

from config import settings

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Error hashing password: {str(e)}")
        raise ValueError("Failed to hash password")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    try:
        return pwd_context.verify(plain, hashed)
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        return False


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    try:
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        payload = {"sub": subject, "exp": expire, "iat": datetime.now(timezone.utc)}
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    except Exception as e:
        logger.error(f"Error creating access token: {str(e)}")
        raise ValueError("Failed to create access token")


def decode_access_token(token: str) -> str:
    """Returns the `sub` (user_id) from a valid token, raises JWTError otherwise."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub: str | None = payload.get("sub")
        if sub is None:
            raise JWTError("Token missing subject")
        return sub
    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error decoding token: {str(e)}")
        raise JWTError("Failed to decode token")


# ── Note Encryption (AES-256-GCM) ────────────────────────────────────────────

def _get_key() -> bytes:
    """Decodes the base64-encoded 32-byte key from settings.
    
    Raises RuntimeError if NOTE_ENCRYPTION_KEY is missing or invalid so that
    misconfiguration is detected at startup rather than silently using a
    trivially known all-zeros key.
    """
    raw = settings.NOTE_ENCRYPTION_KEY
    if not raw or raw.startswith("changeme"):
        raise RuntimeError(
            "NOTE_ENCRYPTION_KEY is not set or is using the placeholder value. "
            "Generate a key with: python -c \"import secrets, base64; "
            "print(base64.b64encode(secrets.token_bytes(32)).decode())\""
        )
    try:
        key = base64.b64decode(raw)
    except Exception as e:
        raise RuntimeError(f"NOTE_ENCRYPTION_KEY is not valid base64: {e}") from e
    if len(key) != 32:
        raise RuntimeError(
            f"NOTE_ENCRYPTION_KEY must decode to exactly 32 bytes, got {len(key)} bytes."
        )
    return key


def encrypt_text(plaintext: str) -> str:
    """Encrypt text using AES-256-GCM. Returns base64(nonce + ciphertext)."""
    try:
        if not plaintext:
            raise ValueError("Cannot encrypt empty text")
        
        key = _get_key()
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
        return base64.b64encode(nonce + ct).decode()
    except Exception as e:
        logger.error(f"Error encrypting text: {str(e)}")
        raise ValueError("Failed to encrypt text")


def decrypt_text(token: str) -> str:
    """Decrypt text using AES-256-GCM."""
    try:
        if not token:
            raise ValueError("Cannot decrypt empty token")
        
        key = _get_key()
        aesgcm = AESGCM(key)
        raw = base64.b64decode(token)
        
        if len(raw) < 12:
            raise ValueError("Invalid token format")
        
        nonce, ct = raw[:12], raw[12:]
        plaintext = aesgcm.decrypt(nonce, ct, None).decode()
        return plaintext
    except Exception as e:
        logger.error(f"Error decrypting text: {str(e)}")
        raise ValueError("Failed to decrypt text")
