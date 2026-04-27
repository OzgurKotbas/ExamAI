"""
models/note.py – Note ORM model. Stores uploaded note content.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    context_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)   # "image" | "pdf" | "text"

    # Encrypted at rest (AES-256-GCM via utils/security.py)
    raw_text_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    cleaned_text_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    ocr_quality_score: Mapped[float | None] = mapped_column(nullable=True)  # 0-1
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notes")
    quizzes: Mapped[list["Quiz"]] = relationship("Quiz", back_populates="note", cascade="all, delete-orphan")
