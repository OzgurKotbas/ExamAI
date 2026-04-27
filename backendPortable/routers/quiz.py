"""
routers/quiz.py – Quiz creation, status polling, SSE updates, and question listing.
"""

import logging
import uuid as _uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models.note import Note
from models.question import Question
from models.quiz import Quiz
from models.user import User
from schemas.question import QuestionRead
from schemas.quiz import QuizCreateRequest, QuizRead, QuizStatusResponse
from services.auth_service import get_current_user
from services.cache_service import _build_cache_key, get_cached_quiz, set_cached_quiz
from utils.security import decrypt_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/quizzes", tags=["Quizzes"])


@router.post("", response_model=QuizStatusResponse, status_code=202)
async def create_quiz(
    body: QuizCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new quiz from a note.
    Returns 202 Accepted immediately; generation runs in background via Celery.
    If an identical quiz (same params) was generated before, returns the cached quiz_id.
    """
    try:
        # Ownership check
        note = await db.get(Note, body.note_id)
        if not note or note.user_id != current_user.id:
            logger.warning(f"Quiz creation failed: Note {body.note_id} not found or not owned by user {current_user.id}")
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Note not found.")

        # Validate note content
        if not note.cleaned_text_encrypted:
            logger.warning(f"Quiz creation failed: Note {body.note_id} has no content")
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Cannot create quiz from note without content. Please ensure the note has been processed."
            )

        # Decrypt and validate note text
        try:
            cleaned_text = decrypt_text(note.cleaned_text_encrypted)
            if not cleaned_text or len(cleaned_text.strip()) < 50:
                logger.warning(f"Quiz creation failed: Note {body.note_id} has insufficient content")
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "Note content is too short to generate meaningful questions. Please add more content to your note."
                )
        except Exception as e:
            logger.error(f"Failed to decrypt note {body.note_id}: {str(e)}")
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Failed to process note content. Please try again."
            )

        uid = str(current_user.id)
        nid = str(body.note_id)

        # Cache check – uses the single canonical key builder from cache_service
        cached = await get_cached_quiz(uid, nid, body.total_questions, body.mc_ratio, body.difficulty)
        if cached:
            logger.info(f"Returning cached quiz for user {uid}, note {nid}")
            return QuizStatusResponse(
                quiz_id=_uuid.UUID(cached["quiz_id"]),
                status="ready",
                message="Quiz fetched from cache.",
            )

        # Canonical cache key (same function as cache_service uses internally)
        cache_key = _build_cache_key(uid, nid, body.total_questions, body.mc_ratio, body.difficulty)

        quiz = Quiz(
            user_id=current_user.id,
            note_id=body.note_id,
            total_questions=body.total_questions,
            mc_ratio=body.mc_ratio,
            difficulty=body.difficulty,
            parameters=body.model_dump(),
            cache_key=cache_key,
        )
        db.add(quiz)
        await db.flush()

        logger.info(f"Created quiz {quiz.id} for user {uid}, note {nid}")

        # Enqueue Celery task
        try:
            from services.celery_tasks import generate_quiz_task
            generate_quiz_task.delay(str(quiz.id), cleaned_text)
        except Exception as e:
            logger.error(f"Failed to enqueue Celery task for quiz {quiz.id}: {str(e)}")
            # Don't fail the request, but mark quiz as failed
            quiz.status = "failed"
            await db.commit()
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Failed to start quiz generation. Please try again."
            )

        # Save to Redis cache so subsequent identical requests return immediately
        await set_cached_quiz(uid, nid, body.total_questions, body.mc_ratio, body.difficulty, quiz_id=str(quiz.id))

        await db.commit()

        return QuizStatusResponse(
            quiz_id=quiz.id,
            status="pending",
            message="Quiz is being generated. Poll /quizzes/{quiz_id}/status for updates.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating quiz: {str(e)}")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to create quiz. Please try again."
        )


@router.get("/{quiz_id}/status", response_model=QuizStatusResponse)
async def quiz_status(
    quiz_id: _uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        quiz = await db.get(Quiz, quiz_id)
        if not quiz or quiz.user_id != current_user.id:
            logger.warning(f"Quiz status check failed: Quiz {quiz_id} not found or not owned by user {current_user.id}")
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Quiz not found.")
        
        msg = {
            "pending": "Quiz is queued for generation.",
            "generating": "Quiz is currently being generated…",
            "ready": "Quiz is ready!",
            "failed": "Quiz generation failed. Please try again.",
        }.get(quiz.status, quiz.status)
        
        return QuizStatusResponse(quiz_id=quiz.id, status=quiz.status, message=msg)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking quiz status for {quiz_id}: {str(e)}")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to check quiz status."
        )


@router.get("/{quiz_id}/questions", response_model=list[QuestionRead])
async def get_questions(
    quiz_id: _uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns questions for a ready quiz (correct_answer is NOT included)."""
    try:
        quiz = await db.get(Quiz, quiz_id)
        if not quiz or quiz.user_id != current_user.id:
            logger.warning(f"Questions retrieval failed: Quiz {quiz_id} not found or not owned by user {current_user.id}")
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Quiz not found.")
        
        if quiz.status != "ready":
            logger.warning(f"Questions retrieval failed: Quiz {quiz_id} not ready (status: {quiz.status})")
            raise HTTPException(status.HTTP_409_CONFLICT, f"Quiz is not ready yet (status: {quiz.status}).")
        
        result = await db.execute(
            select(Question).where(Question.quiz_id == quiz_id).order_by(Question.order_index)
        )
        questions = result.scalars().all()
        
        logger.info(f"Retrieved {len(questions)} questions for quiz {quiz_id}")
        return questions

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving questions for quiz {quiz_id}: {str(e)}")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to retrieve quiz questions."
        )


@router.get("", response_model=list[QuizRead])
async def list_quizzes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = await db.execute(
            select(Quiz).where(Quiz.user_id == current_user.id).order_by(Quiz.created_at.desc())
        )
        quizzes = result.scalars().all()
        
        logger.info(f"Retrieved {len(quizzes)} quizzes for user {current_user.id}")
        return quizzes

    except Exception as e:
        logger.error(f"Error listing quizzes for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to retrieve quizzes."
        )
