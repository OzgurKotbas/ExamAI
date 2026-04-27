"""
models/question.py – Question ORM model.
"""

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), index=True)

    type: Mapped[str] = mapped_column(String(20), nullable=False)   # "multiple_choice" | "open_ended"
    text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[dict | None] = mapped_column(JSON, nullable=True)          # {A:.., B:.., C:.., D:..}
    correct_answer: Mapped[str | None] = mapped_column(String(4), nullable=True)  # "A"/"B"/"C"/"D" (MC only)
    topic: Mapped[str] = mapped_column(String(128), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    rubric: Mapped[str | None] = mapped_column(Text, nullable=True)  # Open-ended scoring guide
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="questions")
    answers: Mapped[list["Answer"]] = relationship("Answer", back_populates="question", cascade="all, delete-orphan")

    # Additional indexes for performance
    __table_args__ = (
        Index('idx_question_quiz_order', 'quiz_id', 'order_index'),
        Index('idx_question_topic', 'topic'),
        Index('idx_question_difficulty', 'difficulty'),
    )
