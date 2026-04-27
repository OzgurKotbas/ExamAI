"""
schemas/quiz.py – Pydantic schemas for Quiz creation and reading.
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class QuizCreateRequest(BaseModel):
    note_id: uuid.UUID
    total_questions: int = Field(10, ge=1, le=50)
    mc_ratio: float = Field(0.7, ge=0.0, le=1.0)   # fraction that are multiple-choice
    difficulty: Literal["easy", "medium", "hard"] = "medium"


class QuizRead(BaseModel):
    id: uuid.UUID
    note_id: uuid.UUID
    total_questions: int
    mc_ratio: float
    difficulty: str
    status: str
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class QuizStatusResponse(BaseModel):
    quiz_id: uuid.UUID
    status: str
    message: str
