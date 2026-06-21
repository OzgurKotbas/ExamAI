"""
main.py – FastAPI application entry point.
"""

import logging
import base64
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from limiter import limiter

from config import settings
from database import init_db, close_db
from utils.logger import get_logger
from routers import auth, quiz, notes
from services.ai_service import _get_hf_models, _get_hf_tokens

logger = get_logger(__name__)

# ── Rate Limiter (slowapi) ────────────────────────────────────────────────────
# Limiter nesnesi döngüsel import'u önlemek için limiter.py'de tanımlanmıştır.
# from limiter import limiter  (yukarıda import edildi)


def _is_configured(value: str | None, *placeholders: str) -> bool:
    if not value:
        return False
    if value.startswith("changeme"):
        return False
    return value not in placeholders


def _is_valid_note_key(value: str | None) -> bool:
    if not _is_configured(value, "your-32-byte-encryption-key-here!!", "BURAYA_FERNET_KEY_GIRINIZ"):
        return False
    try:
        return len(base64.b64decode(value)) == 32
    except Exception:
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting ExamAI backend application...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down ExamAI backend application...")
    
    try:
        # Close database connections
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {str(e)}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered quiz generation platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Attach rate limiter to app state (required by slowapi)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add trusted host middleware for production
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts,
    )


# Exception handlers
@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors."""
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal database error"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "config": {
            "secret_key": _is_configured(settings.SECRET_KEY),
            "note_encryption_key": _is_valid_note_key(settings.NOTE_ENCRYPTION_KEY),
            "note_encryption_fallback": (
                not _is_valid_note_key(settings.NOTE_ENCRYPTION_KEY)
                and _is_configured(settings.SECRET_KEY)
            ),
            "gemini_api_key": _is_configured(settings.GEMINI_API_KEY),
            "huggingface_tokens": len(_get_hf_tokens()),
            "huggingface_models": len(_get_hf_models()),
            "google_oauth": bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET),
            "frontend_url": settings.FRONTEND_URL,
            "allowed_origins": settings.cors_origins,
        },
    }


# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(quiz.router, prefix="/api/v1")
app.include_router(notes.router, prefix="/api/v1", tags=["Notes"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else "Documentation not available in production",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.log_level.lower(),
    )
