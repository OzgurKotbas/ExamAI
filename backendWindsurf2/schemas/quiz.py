"""
schemas/quiz.py – Pydantic schemas for Quiz creation, submission, and grading.
"""

import uuid
from datetime import datetime
from typing import Literal, List, Dict, Any

from pydantic import BaseModel, Field


class QuizCreateRequest(BaseModel):
    note_id: uuid.UUID
    total_questions: int = Field(10, ge=1, le=50)
    mc_ratio: float = Field(0.7, ge=0.0, le=1.0)   # fraction that are multiple-choice
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    language: str = "tr"


class QuizRead(BaseModel):
    id: uuid.UUID
    note_id: uuid.UUID
    total_questions: int
    mc_ratio: float
    difficulty: str
    status: str
    created_at: datetime
    completed_at: datetime | None
    latest_grading_id: uuid.UUID | None = None
    score: float | None = None
    max_score: float | None = None

    model_config = {"from_attributes": True}


class QuizStatusResponse(BaseModel):
    quiz_id: uuid.UUID
    status: str
    message: str
    latest_grading_id: uuid.UUID | None = None


class AnswerSubmission(BaseModel):
    question_id: uuid.UUID
    user_answer: str


class QuizSubmission(BaseModel):
    quiz_id: uuid.UUID
    answers: List[AnswerSubmission]


class GradingResult(BaseModel):
    question_id: uuid.UUID
    score: float
    user_answer: str
    feedback: str
    key_points_covered: List[str]
    missing_points: List[str]
    suggestions: List[str]


class QuizGradingResponse(BaseModel):
    quiz_id: uuid.UUID
    total_score: int
    max_score: int
    percentage: float
    grading_results: List[GradingResult]
    completed_at: datetime


class GradingStatusResponse(BaseModel):
    grading_id: uuid.UUID
    quiz_id: uuid.UUID
    status: Literal["pending", "grading", "completed", "failed"]
    message: str
