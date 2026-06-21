"""
schemas/question.py – Pydantic schemas for Questions.
"""

import uuid
from typing import Literal

from pydantic import BaseModel


class QuestionRead(BaseModel):
    id: uuid.UUID
    quiz_id: uuid.UUID
    type: Literal["multiple_choice", "open_ended"]
    text: str
    options: dict | None       # Only for multiple_choice
    topic: str
    difficulty: str
    rubric: str | None         # Only for open_ended
    order_index: int

    model_config = {"from_attributes": True}


class QuestionReadWithAnswer(QuestionRead):
    """Includes the correct answer; only returned after quiz is submitted."""
    correct_answer: str | None
