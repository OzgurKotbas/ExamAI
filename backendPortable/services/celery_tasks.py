"""
services/celery_tasks.py – Background tasks for quiz generation and processing.
"""

import logging
from typing import Any, Dict

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession

from celery_app import celery_app
from database import AsyncSessionLocal
from models.quiz import Quiz
from models.question import Question
from services.ai_service import generate_questions_from_text

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task class that provides database session management."""
    
    def on_failure(self, exc: Exception, task_id: str, args: tuple, kwargs: Dict[str, Any], einfo: Any) -> None:
        """Handle task failure."""
        logger.error(f"Task {task_id} failed: {str(exc)}")
        super().on_failure(exc, task_id, args, kwargs, einfo)


@celery_app.task(bind=True, base=DatabaseTask, max_retries=3, default_retry_delay=60)
def generate_quiz_task(self, quiz_id: str, note_text: str) -> str:
    """
    Generate quiz questions from note text.
    
    Args:
        quiz_id: UUID of the quiz to generate questions for
        note_text: Decrypted note text content
        
    Returns:
        quiz_id: UUID of the generated quiz
        
    Raises:
        Exception: If quiz generation fails
    """
    import asyncio
    from sqlalchemy import func
    
    logger.info(f"Starting quiz generation for quiz_id: {quiz_id}")
    
    async def _generate_quiz():
        async with AsyncSessionLocal() as db:
            try:
                # Get quiz from database
                quiz = await db.get(Quiz, quiz_id)
                if not quiz:
                    logger.error(f"Quiz {quiz_id} not found")
                    raise ValueError(f"Quiz {quiz_id} not found")
                
                # Update quiz status to generating
                quiz.status = "generating"
                await db.commit()
                
                logger.info(f"Generating {quiz.total_questions} questions for quiz {quiz_id}")
                
                # Generate questions using AI service
                questions_data = await generate_questions_from_text(
                    text=note_text,
                    total_questions=quiz.total_questions,
                    mc_ratio=float(quiz.mc_ratio),
                    difficulty=quiz.difficulty
                )
                
                if not questions_data:
                    logger.error(f"No questions generated for quiz {quiz_id}")
                    quiz.status = "failed"
                    await db.commit()
                    raise ValueError("Failed to generate questions")
                
                # Create question records
                question_objects = []
                for i, q_data in enumerate(questions_data):
                    question = Question(
                        quiz_id=quiz.id,
                        type=q_data["type"],
                        text=q_data["text"],
                        options=q_data.get("options"),
                        correct_answer=q_data.get("correct_answer"),
                        topic=q_data["topic"],
                        difficulty=q_data["difficulty"],
                        rubric=q_data.get("rubric"),
                        order_index=i
                    )
                    question_objects.append(question)
                
                # Bulk insert questions
                db.add_all(question_objects)
                
                # Update quiz status to ready
                quiz.status = "ready"
                quiz.completed_at = func.now()
                
                await db.commit()
                
                logger.info(f"Successfully generated {len(question_objects)} questions for quiz {quiz_id}")
                return quiz_id
                
            except Exception as e:
                logger.error(f"Error generating quiz {quiz_id}: {str(e)}")
                
                # Update quiz status to failed
                try:
                    quiz = await db.get(Quiz, quiz_id)
                    if quiz:
                        quiz.status = "failed"
                        await db.commit()
                except Exception as commit_error:
                    logger.error(f"Failed to update quiz status to failed: {str(commit_error)}")
                
                # Retry if it's a retryable error
                if self.request.retries < self.max_retries:
                    logger.info(f"Retrying quiz generation for {quiz_id} (attempt {self.request.retries + 1})")
                    raise self.retry(countdown=60 * (2 ** self.request.retries))
                else:
                    logger.error(f"Max retries exceeded for quiz {quiz_id}")
                    raise
    
    # Run the async function
    return asyncio.run(_generate_quiz())


@celery_app.task(bind=True, base=DatabaseTask, max_retries=2)
def process_note_task(self, note_id: str, file_path: str, file_type: str) -> str:
    """
    Process uploaded note file (OCR, text extraction, etc.).
    
    Args:
        note_id: UUID of the note to process
        file_path: Path to the uploaded file
        file_type: Type of file (image, pdf, text)
        
    Returns:
        note_id: UUID of the processed note
    """
    import asyncio
    
    logger.info(f"Starting note processing for note_id: {note_id}")
    
    async def _process_note():
        async with AsyncSessionLocal() as db:
            try:
                from models.note import Note
                from services.ocr_service import extract_text_from_file
                
                # Get note from database
                note = await db.get(Note, note_id)
                if not note:
                    logger.error(f"Note {note_id} not found")
                    raise ValueError(f"Note {note_id} not found")
                
                # Extract text from file
                raw_text = await extract_text_from_file(file_path, file_type)
                
                if not raw_text or len(raw_text.strip()) < 10:
                    logger.error(f"No text extracted from file for note {note_id}")
                    raise ValueError("No text extracted from file")
                
                # Clean and process text
                cleaned_text = clean_text(raw_text)
                
                # Encrypt and store
                from utils.security import encrypt_text
                note.raw_text_encrypted = encrypt_text(raw_text)
                note.cleaned_text_encrypted = encrypt_text(cleaned_text)
                
                await db.commit()
                
                logger.info(f"Successfully processed note {note_id}")
                return note_id
                
            except Exception as e:
                logger.error(f"Error processing note {note_id}: {str(e)}")
                
                # Retry if it's a retryable error
                if self.request.retries < self.max_retries:
                    logger.info(f"Retrying note processing for {note_id} (attempt {self.request.retries + 1})")
                    raise self.retry(countdown=30 * (2 ** self.request.retries))
                else:
                    logger.error(f"Max retries exceeded for note {note_id}")
                    raise
    
    return asyncio.run(_process_note())


def clean_text(text: str) -> str:
    """Clean and normalize extracted text."""
    import re
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters that might interfere with AI processing
    text = re.sub(r'[^\w\s\.,!?;:\-\'"()]', ' ', text)
    
    # Normalize line breaks
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()
