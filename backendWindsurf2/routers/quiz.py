import asyncio
import logging
import uuid as _uuid

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models.note import Note
from models.question import Question
from models.quiz import Quiz
from models.user import User
from models.answer import Answer
from models.grading import GradingSession
from schemas.question import QuestionRead, QuestionReadWithAnswer
from schemas.quiz import (
    QuizCreateRequest, QuizRead, QuizStatusResponse,
    QuizSubmission, QuizGradingResponse, GradingStatusResponse
)
from services.auth_service import get_current_user
from services.cache_service import _build_cache_key, get_cached_quiz
from utils.security import decrypt_text
from utils.i18n import translate
from utils.localization import get_localized_feedback

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/quizzes", tags=["Quizzes"])


@router.post("", response_model=QuizStatusResponse, status_code=202)
async def create_quiz(
    body: QuizCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Header("tr", alias="X-Language")
):
    """
    Create a new quiz from a note.
    Returns 202 Accepted immediately; generation runs in background via Celery.
    If an identical quiz (same params + language) was generated before, returns the cached quiz_id.
    Weak topics from previous low-scoring answers are automatically injected for personalization.
    """
    try:
        # Ownership check
        note = await db.get(Note, body.note_id)
        if not note or note.user_id != current_user.id:
            logger.warning(f"Quiz creation failed: Note {body.note_id} not found or not owned by user {current_user.id}")
            raise HTTPException(status.HTTP_404_NOT_FOUND, translate("NOTE_NOT_FOUND", lang))

        # Validate note content
        if not note.cleaned_text_encrypted:
            logger.warning(f"Quiz creation failed: Note {body.note_id} has no content")
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                translate("NOTE_NO_CONTENT", lang)
            )

        # Decrypt and validate note text
        try:
            cleaned_text = decrypt_text(note.cleaned_text_encrypted)
            if not cleaned_text or len(cleaned_text.strip()) < 50:
                logger.warning(f"Quiz creation failed: Note {body.note_id} has insufficient content")
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    translate("NOTE_TOO_SHORT", lang)
                )
        except Exception as e:
            logger.error(f"Failed to decrypt note {body.note_id}: {str(e)}")
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                translate("INTERNAL_SERVER_ERROR", lang)
            )

        uid = str(current_user.id)
        nid = str(body.note_id)
        language = body.language or "tr"

        # ── Personalization: query user's weak topics from Answer table ─────────
        try:
            # Get all quizzes for this user
            user_quiz_ids_res = await db.execute(
                select(Quiz.id).where(Quiz.user_id == current_user.id)
            )
            user_quiz_ids = [r[0] for r in user_quiz_ids_res.fetchall()]

            weak_topics = []
            if user_quiz_ids:
                # Find questions where user scored low (<60% of max possible score)
                # q_score per question ≈ 100 / total_questions ≈ ~10 for 10 questions
                # We use absolute threshold: score < 10 (out of ~10-20 range)
                weak_ans_res = await db.execute(
                    select(Question.topic)
                    .join(Answer, Answer.question_id == Question.id)
                    .where(
                        Answer.user_id == current_user.id,
                        Answer.score < 5,   # Low score threshold
                        Question.quiz_id.in_(user_quiz_ids)
                    )
                    .group_by(Question.topic)
                    .order_by(func.count(Answer.id).desc())
                    .limit(8)
                )
                weak_topics = [row[0] for row in weak_ans_res.fetchall() if row[0]]

            if weak_topics:
                logger.info(f"Personalization active for user {uid}: weak_topics={weak_topics}")
            else:
                logger.info(f"No weak topics found for user {uid} — standard generation")
        except Exception as e:
            logger.warning(f"Failed to query weak topics for user {uid}: {e}")
            weak_topics = []
        # ────────────────────────────────────────────────────────────────────────

        # Cache check – uses the single canonical key builder from cache_service
        cached = await get_cached_quiz(uid, nid, body.total_questions, body.mc_ratio, body.difficulty, language)
        if cached:
            cached_quiz_id = _uuid.UUID(cached["quiz_id"])
            cached_quiz = await db.get(Quiz, cached_quiz_id)
            question_count_res = await db.execute(
                select(func.count(Question.id)).where(Question.quiz_id == cached_quiz_id)
            )
            cached_question_count = question_count_res.scalar() or 0
            if cached_quiz and cached_quiz.status == "ready" and cached_question_count > 0:
                logger.info(f"Returning cached ready quiz for user {uid}, note {nid}")
                return QuizStatusResponse(
                    quiz_id=cached_quiz_id,
                    status="ready",
                    message="Sınav hafızadan (cache) getirildi.",
                )
            logger.warning(
                "Ignoring stale quiz cache | quiz_id=%s | status=%s | questions=%s",
                cached_quiz_id,
                getattr(cached_quiz, "status", None),
                cached_question_count,
            )

        # Canonical cache key (same function as cache_service uses internally)
        cache_key = _build_cache_key(uid, nid, body.total_questions, body.mc_ratio, body.difficulty, language)

        # Convert UUIDs to strings for JSON serialization in parameters
        params = body.model_dump()
        params['note_id'] = str(params['note_id'])
        # Inject weak_topics into parameters so Celery worker can use them
        params['weak_topics'] = weak_topics if weak_topics else None
        params['language'] = language

        quiz = Quiz(
            user_id=current_user.id,
            note_id=body.note_id,
            total_questions=body.total_questions,
            mc_ratio=body.mc_ratio,
            difficulty=body.difficulty,
            parameters=params,
            cache_key=cache_key,
        )
        db.add(quiz)
        await db.flush()   # quiz.id üret (henüz commit yok)

        logger.info(f"Created quiz {quiz.id} for user {uid}, note {nid}")

        # Önce commit et – Celery worker quiz kaydını DB'de görmeli
        await db.commit()

        # Commit tamamlandıktan sonra Celery task'ı kuyruğa al
        try:
            from services.celery_tasks import generate_quiz_task
            generate_quiz_task.delay(str(quiz.id), cleaned_text)
        except Exception as e:
            logger.error(f"Failed to enqueue Celery task for quiz {quiz.id}; using local fallback: {str(e)}")
            try:
                from services.celery_tasks import run_quiz_generation
                task = asyncio.create_task(run_quiz_generation(str(quiz.id), cleaned_text))
                task.add_done_callback(
                    lambda t: logger.error("Local quiz generation fallback failed", exc_info=t.exception())
                    if t.exception()
                    else logger.info(f"Local quiz generation fallback completed for quiz {quiz.id}")
                )
            except Exception as fallback_error:
                logger.error(f"Failed to schedule local quiz generation fallback for quiz {quiz.id}: {fallback_error}")
                quiz.status = "failed"
                await db.commit()
                raise HTTPException(
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Sınav oluşturma başlatılamadı. Lütfen tekrar deneyin."
                )
            else:
                logger.info(f"Scheduled local quiz generation fallback for quiz {quiz.id}")
                return QuizStatusResponse(
                    quiz_id=quiz.id,
                    status="pending",
                    message="Sınav oluşturuluyor. Lütfen bekleyin...",
                )
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
            translate("QUIZ_GEN_FAILED", lang)
        )


@router.get("/{quiz_id}/status", response_model=QuizStatusResponse)
async def quiz_status(
    quiz_id: _uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Header("tr", alias="X-Language")
):
    try:
        quiz = await db.get(Quiz, quiz_id)
        if not quiz or quiz.user_id != current_user.id:
            logger.warning(f"Quiz status check failed: Quiz {quiz_id} not found or not owned by user {current_user.id}")
            raise HTTPException(status.HTTP_404_NOT_FOUND, translate("QUIZ_NOT_FOUND", lang))
        
        msg = {
            "pending": "Sınav oluşturma kuyruğunda bekliyor.",
            "generating": "Sınav şu anda oluşturuluyor...",
            "ready": "Sınav hazır!",
            "failed": "Sınav oluşturulamadı. Lütfen tekrar deneyin.",
        }.get(quiz.status, quiz.status)

        # Find latest completed grading session
        grading_result = await db.execute(
            select(GradingSession.id)
            .where(GradingSession.quiz_id == quiz_id)
            .where(GradingSession.status == "completed")
            .order_by(GradingSession.completed_at.desc())
            .limit(1)
        )
        latest_id = grading_result.scalar_one_or_none()
        
        return QuizStatusResponse(
            quiz_id=quiz.id, 
            status=quiz.status, 
            message=msg,
            latest_grading_id=latest_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking quiz status for {quiz_id}: {str(e)}")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            translate("INTERNAL_SERVER_ERROR", lang)
        )


@router.get("/{quiz_id}/questions", response_model=list[QuestionReadWithAnswer | QuestionRead])
async def get_questions(
    quiz_id: _uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Header("tr", alias="X-Language")
):
    """
    Returns questions for a ready quiz.
    - For Test exams (mc_ratio == 1.0), correct_answer IS included.
    - For Classic/Mixed exams, correct_answer is NOT included until submission.
    """
    try:
        quiz = await db.get(Quiz, quiz_id)
        if not quiz or quiz.user_id != current_user.id:
            logger.warning(f"Questions retrieval failed: Quiz {quiz_id} not found or not owned by user {current_user.id}")
            raise HTTPException(status.HTTP_404_NOT_FOUND, translate("QUIZ_NOT_FOUND", lang))
        
        if quiz.status != "ready":
            logger.warning(f"Questions retrieval failed: Quiz {quiz_id} not ready (status: {quiz.status})")
            raise HTTPException(status.HTTP_409_CONFLICT, f"{translate('QUIZ_NOT_READY', lang)} (durum: {quiz.status}).")
        
        result = await db.execute(
            select(Question).where(Question.quiz_id == quiz_id).order_by(Question.order_index)
        )
        questions = result.scalars().all()
        
        # Check if it's a pure Test (100% Multiple Choice)
        is_test = float(quiz.mc_ratio) == 1.0
        
        if is_test:
            logger.info(f"Retrieved {len(questions)} questions for test quiz {quiz_id} (including answers)")
            return questions # Pydantic will handle the schema (QuestionReadWithAnswer vs QuestionRead)
        else:
            logger.info(f"Retrieved {len(questions)} questions for quiz {quiz_id} (excluding answers)")
            # Manually strip answers or let Pydantic handle it via response_model
            # Since QuestionRead doesn't have correct_answer, it will be stripped
            return questions

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving questions for quiz {quiz_id}: {str(e)}")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            translate("INTERNAL_SERVER_ERROR", lang)
        )


@router.get("", response_model=list[QuizRead])
async def list_quizzes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Header("tr", alias="X-Language")
):
    try:
        # Get quizzes
        result = await db.execute(
            select(Quiz).where(Quiz.user_id == current_user.id).order_by(Quiz.created_at.desc())
        )
        quizzes = result.scalars().all()
        
        response_list = []
        for quiz in quizzes:
            # Find the latest completed grading session
            grading_result = await db.execute(
                select(GradingSession.id)
                .where(GradingSession.quiz_id == quiz.id)
                .where(GradingSession.status == "completed")
                .order_by(GradingSession.completed_at.desc())
                .limit(1)
            )
            latest_id = grading_result.scalar_one_or_none()
            
            score = None
            max_score = None
            if latest_id:
                # Calculate total score from answers for this grading session
                score_result = await db.execute(
                    select(func.sum(Answer.score))
                    .where(Answer.grading_id == latest_id)
                )
                score = score_result.scalar() or 0.0
                max_score = 100.0

            # Build a plain dict — avoids touching ORM __setattr__ trap
            response_list.append({
                "id": quiz.id,
                "note_id": quiz.note_id,
                "total_questions": quiz.total_questions,
                "mc_ratio": float(quiz.mc_ratio),
                "difficulty": quiz.difficulty,
                "status": quiz.status,
                "created_at": quiz.created_at,
                "completed_at": quiz.completed_at,
                "latest_grading_id": latest_id,
                "score": score,
                "max_score": max_score,
            })
        
        logger.info(f"Retrieved {len(response_list)} quizzes for user {current_user.id}")
        return response_list

    except Exception as e:
        logger.error(f"Error listing quizzes for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            translate("INTERNAL_SERVER_ERROR", lang)
        )


@router.post("/{quiz_id}/submit", response_model=GradingStatusResponse)
async def submit_quiz_for_grading(
    quiz_id: _uuid.UUID,
    body: QuizSubmission,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Header("tr", alias="X-Language")
):
    """
    Submit quiz answers for grading.
    If all questions are multiple choice, grades instantly.
    Otherwise, enqueues Celery task for AI grading.
    """
    try:
        from datetime import datetime, timezone
        
        # Validate quiz ownership and status
        quiz = await db.get(Quiz, quiz_id)
        if not quiz or quiz.user_id != current_user.id:
            logger.warning(f"Quiz submission failed: Quiz {quiz_id} not found or not owned by user {current_user.id}")
            raise HTTPException(status.HTTP_404_NOT_FOUND, translate("QUIZ_NOT_FOUND", lang))
        
        if quiz.status != "ready":
            logger.warning(f"Quiz submission failed: Quiz {quiz_id} not ready (status: {quiz.status})")
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"{translate('QUIZ_NOT_READY', lang)} (durum: {quiz.status})."
            )
        
        # Fetch all questions
        result = await db.execute(
            select(Question).where(Question.quiz_id == quiz_id)
        )
        questions = result.scalars().all()
        
        answer_ids = {str(a.question_id) for a in body.answers}
        missing_count = len([q for q in questions if str(q.id) not in answer_ids])
        if missing_count:
            logger.info(f"Quiz submission: {missing_count} questions left unanswered — treating as empty (score 0)")
        
        # Check if any questions require AI grading
        has_open_ended = any(q.type == "open_ended" for q in questions)
        
        # Create grading session
        grading = GradingSession(
            quiz_id=quiz_id,
            user_id=current_user.id,
            total_questions=len(questions),
            status="completed" if not has_open_ended else "pending"
        )
        db.add(grading)
        await db.flush() # Ensure grading.id is populated
        
        user_answers = {str(a.question_id): a.user_answer for a in body.answers}
        
        if not has_open_ended:
            # Get quiz language from parameters
            quiz_lang = quiz.parameters.get('language', 'tr')
            
            # Instant grading for multiple-choice questions
            graded_count = 0
            num_questions = len(questions)
            base_q_score = 100 // num_questions
            last_q_score = 100 - (base_q_score * (num_questions - 1))

            for i, question in enumerate(questions):
                user_answer = user_answers.get(str(question.id), "")
                # Clean answer for comparison (A, B, C, D)
                user_ans_clean = user_answer.strip().upper()
                correct_ans_clean = question.correct_answer.strip().upper() if question.correct_answer else ""

                current_max_score = last_q_score if i == num_questions - 1 else base_q_score
                score = float(current_max_score) if user_ans_clean == correct_ans_clean else 0.0
                
                # Localized feedback
                feedback = get_localized_feedback(quiz_lang, score, question.correct_answer, question.options)
                
                answer = Answer(
                    user_id=current_user.id,
                    question_id=question.id,
                    grading_id=grading.id,
                    user_answer=user_ans_clean,
                    is_ai_graded=False,
                    score=score,
                    feedback=feedback,
                    graded_at=datetime.now(timezone.utc)
                )
                db.add(answer)
                graded_count += 1
            
            grading.graded_questions = graded_count
            grading.status = "completed"
            grading.completed_at = datetime.now(timezone.utc)
            await db.commit()
            
            logger.info(f"Instant grading completed for quiz {quiz_id}")
            return GradingStatusResponse(
                grading_id=grading.id,
                quiz_id=quiz_id,
                status="completed",
                message="Sınav anında değerlendirildi!"
            )
        else:
            # Enqueue Celery task for AI grading
            await db.flush()
            try:
                from services.celery_tasks import grade_quiz_task
                grade_quiz_task.delay(str(grading.id), str(quiz_id), user_answers)
                await db.commit()
                
                logger.info(f"Enqueued AI grading for quiz {quiz_id}")
                return GradingStatusResponse(
                    grading_id=grading.id,
                    quiz_id=quiz_id,
                    status="pending",
                    message="Sınav yapay zeka tarafından değerlendiriliyor. Lütfen bekleyin."
                )
            except Exception as e:
                logger.error(f"Failed to enqueue grading task: {str(e)}")
                grading.status = "failed"
                await db.commit()
                raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Değerlendirme başlatılamadı.")

        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error submitting quiz {quiz_id}: {str(e)}")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            translate("INTERNAL_SERVER_ERROR", lang)
        )


@router.get("/{quiz_id}/grading/{grading_id}", response_model=QuizGradingResponse)
async def get_grading_results(
    quiz_id: _uuid.UUID,
    grading_id: _uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Header("tr", alias="X-Language")
):
    """
    Get grading results for a submitted quiz.
    Returns detailed scores and AI feedback.
    """
    try:
        # Validate grading session ownership
        grading = await db.get(GradingSession, grading_id)
        if not grading or grading.user_id != current_user.id or grading.quiz_id != quiz_id:
            logger.warning(f"Grading results failed: Grading {grading_id} not found or not owned by user {current_user.id}")
            raise HTTPException(status.HTTP_404_NOT_FOUND, translate("GRADING_NOT_FOUND", lang))
        
        if grading.status != "completed":
            logger.warning(f"Grading results failed: Grading {grading_id} not completed (status: {grading.status})")
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"{translate('GRADING_NOT_READY', lang)} (durum: {grading.status})."
            )
        
        # Get all answers for this quiz
        result = await db.execute(
            select(Answer)
            .join(Question)
            .where(Answer.grading_id == grading_id)
            .order_by(Question.order_index)
        )
        answers = result.scalars().all()
        
        if not answers:
            logger.warning(f"No answers found for quiz {quiz_id}")
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                translate("NO_ANSWERS_FOUND", lang)
            )
        
        # Calculate total score (already out of 100 total points)
        total_score = sum(answer.score or 0 for answer in answers)
        max_score = 100.0
        percentage = total_score  # Since max_score is 100
        
        # Format grading results
        grading_results = []
        for answer in answers:
            grading_results.append({
                "question_id": answer.question_id,
                "score": answer.score or 0,
                "user_answer": answer.user_answer,
                "feedback": answer.feedback or "Geri bildirim mevcut değil",
                "key_points_covered": [],
                "missing_points": [],
                "suggestions": []
            })
        
        logger.info(f"Retrieved grading results for quiz {quiz_id}, total_score: {total_score}/{max_score}")
        
        return QuizGradingResponse(
            quiz_id=quiz_id,
            total_score=total_score,
            max_score=max_score,
            percentage=round(percentage, 2),
            grading_results=grading_results,
            completed_at=grading.completed_at or grading.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving grading results for quiz {quiz_id}: {str(e)}")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            translate("INTERNAL_SERVER_ERROR", lang)
        )


@router.get("/{quiz_id}/grading/{grading_id}/status", response_model=GradingStatusResponse)
async def get_grading_status(
    quiz_id: _uuid.UUID,
    grading_id: _uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Header("tr", alias="X-Language")
):
    """
    Get the status of an ongoing grading process.
    """
    try:
        grading = await db.get(GradingSession, grading_id)
        if not grading or grading.user_id != current_user.id or grading.quiz_id != quiz_id:
            logger.warning(f"Grading status check failed: Grading {grading_id} not found or not owned by user {current_user.id}")
            raise HTTPException(status.HTTP_404_NOT_FOUND, translate("GRADING_NOT_FOUND", lang))
        
        msg = {
            "pending": "Sınav değerlendirme kuyruğunda bekliyor.",
            "grading": f"Sınav şu anda değerlendiriliyor... ({grading.graded_questions}/{grading.total_questions} soru işlendi)",
            "completed": "Sınav değerlendirmesi tamamlandı!",
            "failed": f"Değerlendirme başarısız oldu. {grading.error_message or 'Lütfen tekrar deneyin.'}",
        }.get(grading.status, grading.status)
        
        return GradingStatusResponse(
            grading_id=grading.id,
            quiz_id=quiz_id,
            status=grading.status,
            message=msg
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking grading status for {grading_id}: {str(e)}")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            translate("INTERNAL_SERVER_ERROR", lang)
        )


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz(
    quiz_id: _uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Header("tr", alias="X-Language")
):
    """
    Delete a quiz and all its associated questions, answers, and grading sessions.
    """
    try:
        quiz = await db.get(Quiz, quiz_id)
        if not quiz or quiz.user_id != current_user.id:
            logger.warning(f"Delete quiz failed: Quiz {quiz_id} not found or not owned by user {current_user.id}")
            raise HTTPException(status.HTTP_404_NOT_FOUND, translate("QUIZ_NOT_FOUND", lang))

        # SQLAlchemy cascade should handle deleting associated Questions, Answers, GradingSessions
        await db.delete(quiz)
        await db.commit()
        
        logger.info(f"Successfully deleted quiz {quiz_id} by user {current_user.id}")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting quiz {quiz_id}: {str(e)}")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            translate("INTERNAL_SERVER_ERROR", lang)
        )


@router.get("/analytics", response_model=dict)
async def get_quiz_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Header("tr", alias="X-Language")
):
    """
    Get analytics for the authenticated user.
    Returns:
      - overall_score: Average score across all completed quizzes
      - topic_stats: Per-topic accuracy percentages
      - weak_topics: Topics with < 60% accuracy
      - strong_topics: Topics with >= 80% accuracy
      - total_quizzes_completed: Number of completed grading sessions
      - total_questions_answered: Total answered questions
    """
    try:
        # Get all user quiz IDs
        quiz_ids_res = await db.execute(
            select(Quiz.id).where(Quiz.user_id == current_user.id)
        )
        quiz_ids = [r[0] for r in quiz_ids_res.fetchall()]

        if not quiz_ids:
            return {
                "overall_score": 0,
                "topic_stats": [],
                "weak_topics": [],
                "strong_topics": [],
                "total_quizzes_completed": 0,
                "total_questions_answered": 0,
            }

        # Get completed grading sessions count
        grading_count_res = await db.execute(
            select(func.count(GradingSession.id))
            .where(
                GradingSession.user_id == current_user.id,
                GradingSession.status == "completed"
            )
        )
        completed_grading_count = grading_count_res.scalar() or 0

        # Get all answers with topic info for this user
        # We fetch each answer individually (score + topic) to compute correct/total per topic
        answers_res = await db.execute(
            select(
                Question.topic,
                Answer.score,
            )
            .join(Answer, Answer.question_id == Question.id)
            .where(
                Answer.user_id == current_user.id,
                Answer.score.isnot(None),
                Question.quiz_id.in_(quiz_ids)
            )
        )
        rows = answers_res.fetchall()

        # Aggregate per-topic stats
        # accuracy = correct_count / total_count * 100
        # A question is "correct" if score > 0
        topic_data: dict = {}
        total_score_sum = 0.0
        total_ans_count = 0

        for topic, score in rows:
            if not topic:
                continue
            if topic not in topic_data:
                topic_data[topic] = {"total_count": 0, "correct_count": 0, "raw_score_sum": 0.0}
            topic_data[topic]["total_count"] += 1
            topic_data[topic]["raw_score_sum"] += (score or 0)
            if (score or 0) > 0:
                topic_data[topic]["correct_count"] += 1
            total_score_sum += (score or 0)
            total_ans_count += 1

        total_correct_count = sum(d["correct_count"] for d in topic_data.values())

        # Build topic stats list
        topic_stats = []
        weak_topics = []
        strong_topics = []

        for topic, data in topic_data.items():
            if data["total_count"] == 0:
                continue
            # accuracy = doğru cevap sayısı / toplam soru sayısı * 100
            accuracy_pct = round((data["correct_count"] / data["total_count"]) * 100, 1)

            topic_stat = {
                "topic": topic,
                "accuracy": accuracy_pct,
                "total_questions": data["total_count"],
            }
            topic_stats.append(topic_stat)
            
            if accuracy_pct < 40:
                weak_topics.append(topic)
            elif accuracy_pct >= 70:
                strong_topics.append(topic)

        # Sort by accuracy ascending (weakest first)
        topic_stats.sort(key=lambda x: x["accuracy"])

        # Genel Ortalama = (Toplam Doğru / Toplam Soru) * 100
        overall_score = round((total_correct_count / total_ans_count) * 100, 1) if total_ans_count > 0 else 0

        logger.info(f"Analytics for user {current_user.id}: {total_ans_count} answers, {len(topic_stats)} topics")

        return {
            "overall_score": overall_score,
            "topic_stats": topic_stats,
            "weak_topics": weak_topics,
            "strong_topics": strong_topics,
            "total_quizzes_completed": completed_grading_count,
            "total_questions_answered": total_ans_count,
        }

    except Exception as e:
        logger.error(f"Error computing analytics for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            translate("INTERNAL_SERVER_ERROR", lang)
        )
