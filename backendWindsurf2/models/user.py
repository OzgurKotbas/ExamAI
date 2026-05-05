"""
models/user.py – User ORM model.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)  # None for OAuth-only users
    picture_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_google_auth: Mapped[bool] = mapped_column(Boolean, default=False)
    is_oauth_user: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    gemini_api_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    gemini_model: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    notes: Mapped[list["Note"]] = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    quizzes: Mapped[list["Quiz"]] = relationship("Quiz", back_populates="user", cascade="all, delete-orphan")
    answers: Mapped[list["Answer"]] = relationship("Answer", back_populates="user", cascade="all, delete-orphan")
    grading_sessions: Mapped[list["GradingSession"]] = relationship("GradingSession", back_populates="user", cascade="all, delete-orphan")
