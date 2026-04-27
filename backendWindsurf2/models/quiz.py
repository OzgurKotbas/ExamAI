"""
models/quiz.py – Quiz ORM model.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func, Index
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    note_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), index=True)

    # Generation parameters (used as cache key)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    mc_ratio: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)  # 0.0 – 1.0
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)     # easy | medium | hard

    parameters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # raw params snapshot
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | generating | ready | failed
    cache_key: Mapped[str] = mapped_column(String(256), index=True, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="quizzes")
    note: Mapped["Note"] = relationship("Note", back_populates="quizzes")
    questions: Mapped[list["Question"]] = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    grading_sessions: Mapped[list["GradingSession"]] = relationship("GradingSession", back_populates="quiz", cascade="all, delete-orphan")

    # Additional indexes for performance
    __table_args__ = (
        Index('idx_quiz_user_status', 'user_id', 'status'),
        Index('idx_quiz_note_status', 'note_id', 'status'),
        Index('idx_quiz_created_at', 'created_at'),
    )
