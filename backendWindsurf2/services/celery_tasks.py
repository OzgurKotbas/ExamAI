"""
services/celery_tasks.py – Background tasks for quiz generation and grading.
"""

import logging
import asyncio
import celery
from typing import Any, Dict

# Fix for Windows asyncio event loop issues
import nest_asyncio
try:
    nest_asyncio.apply()
except Exception:
    # uvloop (used in production) or other loops that don't support patching.
    # This is safe to ignore in production as we use uvicorn/uvloop which
    # manages the loop correctly for the web process.
    pass

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from celery_app import celery_app
from database import AsyncSessionLocal, engine, get_task_engine
from models.quiz import Quiz
from models.question import Question
from models.answer import Answer
from models.grading import GradingSession
from models.user import User
from models.note import Note
from services.ai_service import generate_questions_from_text, grade_open_ended_answer
from services.cache_service import set_cached_quiz
from services.extraction_service import clean_text as clean_extracted_text
from utils.security import encrypt_text, decrypt_text
from utils.localization import get_localized_feedback

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
    from sqlalchemy import func
    
    logger.info(f"Starting quiz generation for quiz_id: {quiz_id}")
    
    async def _generate_quiz():
        # Create a task-specific engine and session factory
        task_engine = get_task_engine()
        async_session = async_sessionmaker(task_engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as db:
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
                
                # Extract language and weak_topics from quiz parameters
                language = quiz.parameters.get('language', 'tr')
                weak_topics = quiz.parameters.get('weak_topics', None)
                
                logger.info(f"Quiz parameters — lang={language}, weak_topics={weak_topics}")
                
                # Generate questions using AI service (with language + personalization)
                questions_data = await generate_questions_from_text(
                    text=note_text,
                    total_questions=quiz.total_questions,
                    mc_ratio=float(quiz.mc_ratio),
                    difficulty=quiz.difficulty,
                    language=language,
                    weak_topics=weak_topics
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

                await set_cached_quiz(
                    str(quiz.user_id),
                    str(quiz.note_id),
                    quiz.total_questions,
                    float(quiz.mc_ratio),
                    quiz.difficulty,
                    quiz_id=str(quiz.id),
                    language=language,
                )
                
                logger.info(f"Successfully generated {len(question_objects)} questions for quiz {quiz_id}")
                return quiz_id
                
            except Exception as e:
                logger.error(f"Error generating quiz {quiz_id}: {str(e)}")
                # Update quiz status to failed
                try:
                    quiz = await db.get(Quiz, quiz_id)
                    if quiz:
                        quiz.status = "failed"
                        params = dict(quiz.parameters or {})
                        params["generation_error"] = str(e)[:500]
                        quiz.parameters = params
                        await db.commit()
                except:
                    pass
                raise
            finally:
                # Explicitly dispose the task-specific engine
                await task_engine.dispose()

    # Run the async function with proper loop management
    try:
        return asyncio.run(run_quiz_generation(quiz_id, note_text))
    except Exception as e:
        if "Retry" in str(e) or isinstance(e, celery.exceptions.Retry):
            raise
        logger.error(f"Fatal error in generate_quiz_task: {str(e)}")
        raise


async def run_quiz_generation(quiz_id: str, note_text: str) -> str:
    """Generate quiz questions using a fresh DB engine.

    Shared by Celery workers and the web-process fallback used when the broker
    cannot accept a task.
    """
    from sqlalchemy import func

    task_engine = get_task_engine()
    async_session = async_sessionmaker(task_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            quiz = await db.get(Quiz, quiz_id)
            if not quiz:
                logger.error(f"Quiz {quiz_id} not found")
                raise ValueError(f"Quiz {quiz_id} not found")

            quiz.status = "generating"
            await db.commit()

            logger.info(f"Generating {quiz.total_questions} questions for quiz {quiz_id}")

            language = quiz.parameters.get("language", "tr")
            weak_topics = quiz.parameters.get("weak_topics", None)

            logger.info(f"Quiz parameters - lang={language}, weak_topics={weak_topics}")

            questions_data = await generate_questions_from_text(
                text=note_text,
                total_questions=quiz.total_questions,
                mc_ratio=float(quiz.mc_ratio),
                difficulty=quiz.difficulty,
                language=language,
                weak_topics=weak_topics,
            )

            if not questions_data:
                logger.error(f"No questions generated for quiz {quiz_id}")
                quiz.status = "failed"
                await db.commit()
                raise ValueError("Failed to generate questions")

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
                    order_index=i,
                )
                question_objects.append(question)

            db.add_all(question_objects)

            quiz.status = "ready"
            quiz.completed_at = func.now()

            await db.commit()

            await set_cached_quiz(
                str(quiz.user_id),
                str(quiz.note_id),
                quiz.total_questions,
                float(quiz.mc_ratio),
                quiz.difficulty,
                quiz_id=str(quiz.id),
                language=language,
            )

            logger.info(f"Successfully generated {len(question_objects)} questions for quiz {quiz_id}")
            return quiz_id

        except Exception as e:
            logger.error(f"Error generating quiz {quiz_id}: {str(e)}")
            try:
                quiz = await db.get(Quiz, quiz_id)
                if quiz:
                    quiz.status = "failed"
                    params = dict(quiz.parameters or {})
                    params["generation_error"] = str(e)[:500]
                    quiz.parameters = params
                    await db.commit()
            except Exception:
                logger.exception("Failed to persist quiz generation failure state")
            raise
        finally:
            await task_engine.dispose()


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
    logger.info(f"Starting note processing for note_id: {note_id}")
    
    async def _process_note():
        task_engine = get_task_engine()
        async_session = async_sessionmaker(task_engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as db:
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
                cleaned_text = clean_extracted_text(raw_text)
                
                # Encrypt and store
                note.raw_text_encrypted = encrypt_text(raw_text)
                note.cleaned_text_encrypted = encrypt_text(cleaned_text)
                
                await db.commit()
                
                logger.info(f"Successfully processed note {note_id}")
                return note_id
                
            except Exception as e:
                logger.error(f"Error processing note {note_id}: {str(e)}")
                raise
            finally:
                await task_engine.dispose()
    
    # Run the async function with proper loop management
    try:
        return asyncio.run(_process_note())
    except Exception as e:
        if "Retry" in str(e) or isinstance(e, celery.exceptions.Retry):
            raise
        logger.error(f"Fatal error in process_note_task: {str(e)}")
        raise


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



@celery_app.task(bind=True, base=DatabaseTask, max_retries=3, default_retry_delay=60)
def grade_quiz_task(self, grading_id: str, quiz_id: str, user_answers: Dict[str, str]) -> str:
    """
    Grade quiz answers using AI for open-ended questions.
    Delegates all async work to run_quiz_grading() to avoid nested-closure
    issues with asyncio.run() + uvloop in production.
    """
    logger.info(f"Starting quiz grading for grading_id: {grading_id}")
    try:
        return asyncio.run(run_quiz_grading(grading_id, quiz_id, user_answers))
    except Exception as e:
        if "Retry" in str(e) or isinstance(e, celery.exceptions.Retry):
            raise
        logger.error(f"Fatal error in grade_quiz_task: {str(e)}")
        raise


async def run_quiz_grading(grading_id: str, quiz_id: str, user_answers: Dict[str, str]) -> str:
    """
    Async implementation of quiz grading.
    Shared between the Celery worker and any direct async callers.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from datetime import datetime, timezone

    task_engine = get_task_engine()
    async_session = async_sessionmaker(task_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            # Get grading session
            grading = await db.get(GradingSession, grading_id)
            if not grading:
                raise ValueError(f"Grading session {grading_id} not found")

            # Update status to grading so the frontend shows progress
            grading.status = "grading"
            await db.commit()

            # Get quiz with questions
            result = await db.execute(
                select(Quiz)
                .where(Quiz.id == quiz_id)
                .options(selectinload(Quiz.questions).selectinload(Question.quiz))
            )
            quiz = result.scalar_one_or_none()
            if not quiz:
                raise ValueError(f"Quiz {quiz_id} not found")

            # Get note content for AI context
            from models.note import Note
            note_result = await db.execute(select(Note).where(Note.id == quiz.note_id))
            note = note_result.scalar_one_or_none()
            if not note:
                raise ValueError(f"Note {quiz.note_id} not found")

            note_content = decrypt_text(note.cleaned_text_encrypted)

            # Points per question (all questions sum to 100)
            q_score = 100.0 / len(quiz.questions) if quiz.questions else 0
            quiz_lang = quiz.parameters.get("language", "tr")

            total_score = 0.0
            graded_count = 0

            for question in quiz.questions:
                question_id_str = str(question.id)
                user_answer = user_answers.get(question_id_str, "")

                answer = Answer(
                    user_id=grading.user_id,
                    question_id=question.id,
                    grading_id=grading.id,
                    user_answer=user_answer,
                    is_ai_graded=(question.type == "open_ended"),
                )
                db.add(answer)

                # ── Empty answer: score 0, no AI call ──────────────────────
                if not user_answer.strip():
                    answer.score = 0
                    if question.type == "multiple_choice":
                        answer.feedback = get_localized_feedback(
                            quiz_lang, 0, question.correct_answer, question.options
                        )
                    else:
                        answer.feedback = (
                            "Cevap girilmedi." if quiz_lang == "tr" else "No answer provided."
                        )
                    answer.graded_at = datetime.now(timezone.utc)

                # ── Multiple-choice: instant comparison ─────────────────────
                elif question.type == "multiple_choice":
                    is_correct = (
                        user_answer.strip().upper() == (question.correct_answer or "").upper()
                    )
                    score = q_score if is_correct else 0.0
                    answer.score = score
                    answer.feedback = get_localized_feedback(
                        quiz_lang, score, question.correct_answer, question.options
                    )
                    answer.graded_at = datetime.now(timezone.utc)

                # ── Open-ended: AI grading ──────────────────────────────────
                elif question.type == "open_ended":
                    try:
                        grading_result = await grade_open_ended_answer(
                            question.text,
                            user_answer,
                            note_content,
                            question.rubric,
                            language=quiz_lang,
                        )
                        ai_score = grading_result.get("score", 0)
                        normalized_score = (ai_score / 100.0) * q_score
                        answer.score = normalized_score
                        answer.feedback = grading_result.get(
                            "feedback", "No feedback available."
                        )
                        answer.graded_at = datetime.now(timezone.utc)
                    except Exception as e:
                        logger.error(f"Error grading open-ended answer for question {question.id}: {e}")
                        answer.score = 0
                        answer.feedback = (
                            "Teknik sorun nedeniyle değerlendirilemedi."
                            if quiz_lang == "tr"
                            else "Failed to grade answer due to a technical issue."
                        )
                        answer.graded_at = datetime.now(timezone.utc)

                total_score += answer.score or 0
                graded_count += 1
                grading.graded_questions = graded_count
                # Commit after every question so the frontend can show progress
                await db.commit()

            # Mark grading as completed
            grading.status = "completed"
            grading.completed_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info(
                f"Grading completed | grading_id={grading_id} | score={total_score}/100"
            )
            return grading_id

        except Exception as e:
            logger.error(f"Error during grading of quiz {quiz_id}: {e}")
            try:
                grading = await db.get(GradingSession, grading_id)
                if grading:
                    grading.status = "failed"
                    grading.error_message = str(e)[:500]
                    await db.commit()
            except Exception:
                logger.exception("Could not persist grading failure state")
            raise
        finally:
            await task_engine.dispose()
