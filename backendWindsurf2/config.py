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
    # Explicit credentials — used to bypass asyncpg URL parser stripping Supabase project ref
    SUPABASE_AUTH_USER: str = ""
    SUPABASE_AUTH_PASS: str = ""
    
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

    # ── Hugging Face ───────────────────────────────────────────────────────────
    HUGGINGFACE_API_TOKENS: str = ""
    HUGGINGFACE_API_KEY: str = ""
    HF_TOKEN: str = ""
    HUGGINGFACE_MODELS: str = "Qwen/Qwen2.5-72B-Instruct,Qwen/Qwen2.5-7B-Instruct,mistralai/Mistral-Nemo-Instruct-2407,microsoft/Phi-3.5-mini-instruct,01-ai/Yi-1.5-34B-Chat"

    # ── Specific Model URLs (Optional Overrides) ──────────────────────────────
    MODEL_QWEN_72B: str = ""
    MODEL_QWEN_7B: str = ""
    MODEL_MISTRAL_NEMO: str = ""
    MODEL_PHI_3_5: str = ""
    MODEL_YI_34B: str = ""

    # ── Google Cloud Vision ────────────────────────────────────────────────────
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    # ── Tesseract OCR ────────────────────────────────────────────────────────
    # Optional direct path to tesseract executable. If empty, uses shutil.which()
    TESSERACT_CMD_PATH: str | None = None


    # ── Email (SMTP) ────────────────────────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "ExamAI <noreply@examai.com>"
    FRONTEND_URL: str = "http://localhost:5173"

    # ── Password Reset ─────────────────────────────────────────────────────────
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
    RESET_CODE_EXPIRE_MINUTES: int = 10

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
    
    # ── Note Encryption ─────────────────────────────────────────────────────────
    NOTE_ENCRYPTION_KEY: str = "your-32-byte-encryption-key-here!!"

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
