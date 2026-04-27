"""
config.py – Application settings via Pydantic-Settings.
All values can be overridden through the .env file.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Application ────────────────────────────────────────────────────────────
    APP_NAME: str = "ExamAI"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # ── Security ───────────────────────────────────────────────────────────────
    SECRET_KEY: str = "changeme-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Database ───────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://examai_user:password@localhost:5432/examai_db"
    
    # ── Database Connection Pool ───────────────────────────────────────────────
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    # ── Redis ──────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Google OAuth ───────────────────────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # ── Gemini AI ──────────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # ── Google Cloud Vision ────────────────────────────────────────────────────
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    # ── Encryption ─────────────────────────────────────────────────────────────
    NOTE_ENCRYPTION_KEY: str = ""

    # ── CORS ───────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    # ── Trusted Hosts ────────────────────────────────────────────────────────────
    # Comma-separated list of allowed Host header values for production.
    # Example: "example.com,*.example.com"
    ALLOWED_HOSTS: str = "localhost"

    @property
    def allowed_hosts(self) -> list[str]:
        return [h.strip() for h in self.ALLOWED_HOSTS.split(",")]

    # ── File Upload ─────────────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 20
    UPLOAD_DIR: str = "uploads"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # ── Production Settings ────────────────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def log_level(self) -> str:
        return "INFO" if self.is_production else "DEBUG"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
