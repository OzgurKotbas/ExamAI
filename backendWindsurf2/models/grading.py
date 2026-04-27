"""
models/grading.py – Grading session ORM model for tracking AI grading progress.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class GradingSession(Base):
    __tablename__ = "grading_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)

    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, grading, completed, failed
    total_questions: Mapped[int] = mapped_column(nullable=False)
    graded_questions: Mapped[int] = mapped_column(default=0)
    
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="grading_sessions")
    user: Mapped["User"] = relationship("User", back_populates="grading_sessions")

    # Indexes for performance
    __table_args__ = (
        Index('idx_grading_session_quiz_user', 'quiz_id', 'user_id'),
        Index('idx_grading_session_status', 'status'),
        Index('idx_grading_session_created_at', 'created_at'),
    )
