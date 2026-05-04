"""
services/ai_service.py – AI service integration for quiz generation with HF and Gemini fallback.
"""

import logging
import json
import re
import asyncio
import random
from dataclasses import dataclass
from typing import List, Dict, Any

import httpx
import google.generativeai as genai
from google.api_core import exceptions
from config import settings

logger = logging.getLogger(__name__)


@dataclass
class AIProviderError:
    provider: str
    error: str


def _get_hf_tokens() -> List[str]:
    """Parse HUGGINGFACE_API_TOKENS from config."""
    raw_tokens = [
        settings.HUGGINGFACE_API_TOKENS,
        settings.HUGGINGFACE_API_KEY,
        settings.HF_TOKEN,
    ]
    tokens: list[str] = []
    for raw in raw_tokens:
        if not raw:
            continue
        tokens.extend([t.strip() for t in raw.split(",") if t.strip()])
    return list(dict.fromkeys(tokens))


def _get_hf_models() -> List[str]:
    """Parse HUGGINGFACE_MODELS and specific model variables from config."""
    models = []
    
    # 1. Check comma-separated list
    if settings.HUGGINGFACE_MODELS:
        models.extend([m.strip() for m in settings.HUGGINGFACE_MODELS.split(",") if m.strip()])
    
    # 2. Add specific overrides if defined (and not already in list)
    overrides = [
        settings.MODEL_QWEN_72B,
        settings.MODEL_QWEN_7B,
        settings.MODEL_MISTRAL_NEMO,
        settings.MODEL_PHI_3_5,
        settings.MODEL_YI_34B
    ]
    for o in overrides:
        if o and o not in models:
            models.append(o)
            
    return models


async def _call_hf_api_with_token(model_id: str, token: str, prompt: str, max_new_tokens: int = 4000) -> str:
    """Make a single call to HF Router (OpenAI compatible)."""
    url = "https://router.huggingface.co/v1/chat/completions"
    
    # Extract model name if model_id is a URL
    model_name = model_id
    if model_id.startswith("http"):
        # e.g. https://.../models/Qwen/Qwen2.5-72B-Instruct -> Qwen/Qwen2.5-72B-Instruct
        parts = model_id.split("/models/")
        if len(parts) > 1:
            model_name = parts[1]
        else:
            # Fallback for other URL types
            model_name = model_id.split("/")[-1]

    headers = {"Authorization": f"Bearer {token.strip()}"}
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_new_tokens,
        "temperature": 0.7,
        "stream": False
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code == 429:
                raise ValueError(f"HF Rate limit exceeded for model {model_name}")
            if response.status_code == 503:
                raise ValueError(f"HF Model {model_name} is loading/unavailable")
            
            response.raise_for_status()
            result = response.json()
            
            # OpenAI format response choice
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                if "message" in choice:
                    return choice["message"].get("content", "")
            
            return str(result)
        except Exception as e:
            logger.warning(f"HF API Error ({model_name}): {str(e)}")
            raise


async def _generate_with_fallback(prompt: str, max_tokens: int = 4000, user_api_key: str | None = None) -> str:
    """Try User's Gemini API key first if available, otherwise fallback to HF then system Gemini."""
    errors: list[AIProviderError] = []

    # 1. PRIORITY: If user has their own API key, use it immediately
    if user_api_key:
        try:
            logger.info("User-provided Gemini API key found. Using it as primary provider.")
            generation_config = {
                "temperature": 0.7,
                "max_output_tokens": 8192,
            }
            response = await _call_gemini_with_retry(prompt, generation_config, api_key=user_api_key)
            text = (response.text or "").strip()
            if text:
                return text
            errors.append(AIProviderError("user_gemini", "empty response"))
        except Exception as e:
            logger.warning(f"User's Gemini API key failed: {str(e)}. Falling back to system providers.")
            errors.append(AIProviderError("user_gemini", str(e)))

    # 2. Hugging Face Models (Only if user key didn't return a result or doesn't exist)
    tokens = _get_hf_tokens()
    models = _get_hf_models()

    if tokens and models:
        for model in models:
            for token in tokens:
                try:
                    logger.info(f"Attempting HF generation | model={model}")
                    text = await _call_hf_api_with_token(model, token, prompt, max_tokens)
                    if text and len(text.strip()) > 10:
                        return text
                except Exception as e:
                    logger.warning(f"HF attempt failed | model={model} | error={str(e)}")
                    errors.append(AIProviderError(f"huggingface:{model}", str(e)))
                    continue
    
    # 3. Final Fallback: System Gemini API Key
    if settings.GEMINI_API_KEY:
        try:
            logger.info("HF failed or not configured. Attempting system Gemini fallback.")
            generation_config = {
                "temperature": 0.7,
                "max_output_tokens": 8192,
            }
            # user_api_key was already tried, so we use settings.GEMINI_API_KEY explicitly
            response = await _call_gemini_with_retry(prompt, generation_config, api_key=settings.GEMINI_API_KEY)
            text = (response.text or "").strip()
            if text:
                return text
            errors.append(AIProviderError("system_gemini", "empty response"))
        except Exception as e:
            logger.error("Final system Gemini fallback failed. error=%s", e)
            errors.append(AIProviderError("system_gemini", str(e)))

    error_text = "; ".join(f"{item.provider}: {item.error}" for item in errors[-5:])
    raise ValueError(f"All AI providers failed. {error_text}")


async def generate_questions_from_text(
    text: str,
    total_questions: int,
    mc_ratio: float,
    difficulty: str,
    language: str = "tr",
    weak_topics: List[str] | None = None,
    user_api_key: str | None = None
) -> List[Dict[str, Any]]:
    """Generate quiz questions from text using HF (with fallback) or Gemini.
    
    Args:
        text: Note content to generate questions from.
        total_questions: Total number of questions to generate.
        mc_ratio: Fraction of multiple-choice questions (0.0-1.0).
        difficulty: Difficulty level (easy, medium, hard).
        language: Language for questions and answers ('tr' or 'en').
        weak_topics: List of topics the user has struggled with previously.
        user_api_key: User's personal Gemini API key.
    """
    try:
        # Calculate numbers
        mc_count = int(total_questions * mc_ratio)
        oe_count = total_questions - mc_count
        
        # Build prompt with language and personalization
        prompt = _build_quiz_prompt(text, mc_count, oe_count, difficulty, language, weak_topics)
        
        # Call AI with fallback
        generated_text = await _generate_with_fallback(prompt, user_api_key=user_api_key)
        _log_prompt("QUIZ_GENERATION", prompt, response=generated_text)
        
        # Parse JSON response
        try:
            # Try to find JSON array
            cleaned_response = generated_text.strip()
            cleaned_response = re.sub(r"^```(?:json)?\s*", "", cleaned_response)
            cleaned_response = re.sub(r"\s*```$", "", cleaned_response)
            json_match = re.search(r'\[.*\]', cleaned_response, re.DOTALL)
            if json_match:
                questions = json.loads(json_match.group())
            else:
                questions = json.loads(cleaned_response)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse AI response: {generated_text[:500]}...")
            raise ValueError("Could not parse JSON response from AI")

        # Validate and format questions
        formatted_questions = _format_questions(questions, mc_count, oe_count)
        
        logger.info(f"Generated {len(formatted_questions)} questions (lang={language}, weak_topics={weak_topics})")
        return formatted_questions
        
    except Exception as e:
        logger.error(f"Error generating questions: {str(e)}")
        raise ValueError(f"Failed to generate questions: {str(e)}")


async def grade_open_ended_answer(
    question_text: str,
    user_answer: str,
    note_content: str,
    rubric: str | None = None,
    language: str = "tr",
    user_api_key: str | None = None
) -> Dict[str, Any]:
    """Grade an open-ended answer using AI (Gemini first, then HF fallback)."""
    try:
        # Build grading prompt
        prompt = _build_grading_prompt(question_text, user_answer, note_content, rubric, language)

        # Use the same Gemini-first fallback chain as question generation
        generated_text = await _generate_with_fallback(prompt, max_tokens=2000, user_api_key=user_api_key)

        # Log the interaction
        _log_prompt("GRADING", prompt, response=generated_text)

        # Parse JSON response – strip markdown fences if present
        try:
            cleaned = generated_text.strip()
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if json_match:
                grading_result = json.loads(json_match.group())
            else:
                grading_result = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse grading response: {generated_text[:300]}")
            raise ValueError("Could not parse JSON response from AI")

        # Ensure required fields exist with safe defaults
        if "score" not in grading_result:
            grading_result["score"] = 0
        if "feedback" not in grading_result:
            grading_result["feedback"] = "Degerlendirme tamamlandi." if language == "tr" else "Evaluation complete."

        return grading_result

    except Exception as e:
        logger.error(f"Error grading answer: {str(e)}")
        raise ValueError("Failed to grade answer")



def _build_quiz_prompt(
    text: str,
    mc_count: int,
    oe_count: int,
    difficulty: str,
    language: str = "tr",
    weak_topics: List[str] | None = None
) -> str:
    """Build the prompt for AI with language and personalization support."""
    
    if language == "tr":
        lang_instruction = "Türkçe"
        lang_note = "Tüm soru metinleri, seçenekler ve cevaplar TÜRKÇE olmalıdır."
        difficulty_map = {"easy": "kolay", "medium": "orta", "hard": "zor"}
        diff_label = difficulty_map.get(difficulty, difficulty)
        topic_field = "Konu"
        rubric_field = "Puanlama kriteri"
    else:
        lang_instruction = "English"
        lang_note = "All question texts, options and answers MUST be in ENGLISH."
        difficulty_map = {"easy": "easy", "medium": "medium", "hard": "hard"}
        diff_label = difficulty_map.get(difficulty, difficulty)
        topic_field = "Topic"
        rubric_field = "Scoring criteria"

    # Personalization directive for weak topics
    personalization = ""
    if weak_topics:
        topics_str = ", ".join(weak_topics[:8])  # Limit to 8 topics
        if language == "tr":
            personalization = f"""\nÖNEMLİ KİŞİSELLEŞTİRME: Kullanıcı geçmişte aşağıdaki konularda düşük puan almıştır. \
Bu konulardan daha fazla soru ekle (toplam soruların en az %60'ı bu konulardan olsun):\n{topics_str}\n"""
        else:
            personalization = f"""\nIMPORTANT PERSONALIZATION: The user has previously performed poorly on the following topics. \
Include more questions from these topics (at least 60% of total questions should cover these):\n{topics_str}\n"""

    return f"""Generate a quiz in {lang_instruction} based on the following text.
{lang_note}
The quiz should contain {mc_count} multiple choice questions and {oe_count} open-ended questions.
All questions should be {diff_label} difficulty level.
{personalization}
Text:
{text}

Generate the questions in the following JSON format and return ONLY the JSON array:
[
    {{
        "type": "multiple_choice",
        "text": "Question text in {lang_instruction}",
        "options": {{"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}},
        "correct_answer": "A",
        "topic": "{topic_field} name",
        "difficulty": "{diff_label}"
    }},
    {{
        "type": "open_ended",
        "text": "Question text in {lang_instruction}",
        "topic": "{topic_field} name",
        "difficulty": "{diff_label}",
        "rubric": "{rubric_field} for this question"
    }}
]

IMPORTANT: Return ONLY the JSON array. No explanations.
"""


def _build_grading_prompt(question_text: str, user_answer: str, note_content: str, rubric: str | None, language: str = "tr") -> str:
    """Build the prompt for AI grading, using the most relevant section of the note."""
    lang_instruction = "Turkish" if language == "tr" else "English"
    lang_strict = (
        "ZORUNLU: Tüm geri bildiriminiz, puanlama gerekçeniz ve açıklamalarınız TÜRKÇE olmalıdır. İngilizce kullanmayın."
        if language == "tr" else
        "MANDATORY: All your feedback, scoring rationale and explanations MUST be in ENGLISH. Do NOT use any other language."
    )

    # Extract the most relevant section from the note (keyword matching)
    relevant_context = _extract_relevant_context(question_text, note_content, max_chars=2000)

    prompt = f"""You are an expert academic grader. Grade the student's answer based on the provided course note context.
{lang_strict}

Question: {question_text}
Student's Answer: {user_answer}

Relevant Course Note Context:
---
{relevant_context}
---
"""
    if rubric:
        prompt += f"Grading Rubric / Puanlama Kriteri: {rubric}\n"

    prompt += """
Return ONLY a JSON object in this exact format:
{
    "score": <integer 0-100>,
    "feedback": "<Detailed feedback in the required language>",
    "key_points_covered": ["<Point 1>", "<Point 2>"],
    "missing_points": ["<Missing point 1>"],
    "suggestions": ["<Suggestion 1>"]
}
IMPORTANT: Return ONLY the JSON object. No additional text.
"""
    return prompt


def _extract_relevant_context(question_text: str, note_content: str, max_chars: int = 2000) -> str:
    """Extract the most relevant paragraphs from note_content based on question keywords."""
    if not note_content:
        return ""

    # Split into paragraphs
    import re
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n|\n{2,}', note_content) if p.strip()]
    if not paragraphs:
        # Fall back to character slice
        return note_content[:max_chars]

    # Extract keywords from the question (simple approach: words longer than 3 chars)
    question_words = set(
        w.lower() for w in re.findall(r'\w+', question_text)
        if len(w) > 3
    )

    # Score each paragraph by keyword overlap
    scored = []
    for para in paragraphs:
        para_lower = para.lower()
        score = sum(1 for kw in question_words if kw in para_lower)
        scored.append((score, para))

    # Sort by relevance (descending)
    scored.sort(key=lambda x: x[0], reverse=True)

    # Collect paragraphs until max_chars is reached
    result_parts = []
    total_chars = 0
    for _, para in scored:
        if total_chars + len(para) > max_chars:
            break
        result_parts.append(para)
        total_chars += len(para)

    if not result_parts:
        return note_content[:max_chars]

    return "\n\n".join(result_parts)


async def _call_gemini_with_retry(prompt: str, generation_config: Dict[str, Any], max_retries: int = 3, api_key: str | None = None):
    """Call Gemini API with an exhaustive list of models and multi-version (v1/v1beta) discovery."""
    effective_api_key = api_key or settings.GEMINI_API_KEY
    if not effective_api_key:
        raise ValueError("Gemini API key not configured")
        
    api_versions = ["v1beta", "v1"]
    last_exception = None

    for version in api_versions:
        try:
            logger.info(f"Configuring Gemini SDK with API version: {version}")
            genai.configure(api_key=effective_api_key, transport="rest") # REST is more stable for version switching
            
            # 1. Exhaustive list of potential model names
            models_to_try = [
                settings.GEMINI_MODEL,
                "gemini-1.5-flash",
                "gemini-1.5-flash-latest",
                "gemini-1.5-flash-001",
                "gemini-1.5-flash-002",
                "gemini-1.5-pro",
                "gemini-1.5-pro-latest",
                "gemini-1.5-pro-001",
                "gemini-1.5-pro-002",
                "gemini-pro",
                "gemini-1.0-pro"
            ]
            
            # Clean duplicates
            models_to_try = [m for m in dict.fromkeys(models_to_try) if m]

            # Try the hardcoded list for this version
            for model_name in models_to_try:
                try:
                    logger.info(f"[{version}] Attempting model: {model_name}")
                    # In newer SDKs, we might need to specify the version in the model call if global config isn't enough
                    model = genai.GenerativeModel(model_name)
                    
                    retry_delay = 5
                    for attempt in range(max_retries + 1):
                        try:
                            # Note: The SDK doesn't always respect the global version for generate_content_async 
                            # in older versions, but we'll try the standard way first.
                            return await model.generate_content_async(prompt, generation_config=generation_config)
                        except (exceptions.ResourceExhausted, exceptions.ServiceUnavailable) as e:
                            if attempt < max_retries:
                                wait_time = (retry_delay * (2 ** attempt)) + (random.random() * 2)
                                logger.warning(f"[{version}] Rate limit/service error ({model_name}). Retrying...")
                                await asyncio.sleep(wait_time)
                            else:
                                raise
                    # Success!
                    return 
                    
                except exceptions.NotFound:
                    logger.warning(f"[{version}] Model {model_name} not found (404).")
                    continue 
                except Exception as e:
                    logger.error(f"[{version}] Error with {model_name}: {str(e)}")
                    last_exception = e
                    if "401" in str(e) or "403" in str(e): raise # Auth errors are terminal
                    continue

            # 2. Dynamic Discovery for this version
            try:
                logger.info(f"[{version}] Attempting dynamic model discovery...")
                # genai.list_models() usually respects the global version
                available_models = genai.list_models()
                for m in available_models:
                    if 'generateContent' in m.supported_generation_methods:
                        try:
                            logger.info(f"[{version}] Trying discovered model: {m.name}")
                            model = genai.GenerativeModel(m.name)
                            return await model.generate_content_async(prompt, generation_config=generation_config)
                        except Exception:
                            continue
            except Exception as e:
                logger.warning(f"[{version}] Discovery failed: {e}")

        except Exception as e:
            logger.error(f"Failed to configure or use Gemini with version {version}: {e}")
            last_exception = e

    if last_exception:
        raise last_exception
    raise ValueError("All Gemini versions, models, and discovery attempts failed with 404/Not Found.")


def _format_questions(questions: List[Dict[str, Any]], mc_count: int, oe_count: int) -> List[Dict[str, Any]]:
    """Validate and format generated questions."""
    formatted = []
    for q in questions:
        if not all(key in q for key in ["type", "text", "topic", "difficulty"]):
            continue
        if q["type"] not in ["multiple_choice", "open_ended"]:
            continue
        if q["type"] == "multiple_choice":
            if "options" not in q or "correct_answer" not in q:
                continue
        formatted.append(q)
    return formatted[:(mc_count + oe_count)]


def _log_prompt(prompt_type: str, prompt: str, response: str = ""):
    """
    Log the AI prompt and response for auditing and analysis.
    Stored in logs/prompts.log with a clear format.
    """
    import os
    from datetime import datetime
    
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    log_file = os.path.join(log_dir, "prompts.log")
    
    try:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"================================================================================\n")
            f.write(f"[{timestamp}] TYPE: {prompt_type}\n")
            f.write(f"----------------------------------- PROMPT -------------------------------------\n")
            f.write(f"{prompt.strip()}\n")
            if response:
                f.write(f"---------------------------------- RESPONSE ------------------------------------\n")
                f.write(f"{response.strip()}\n")
            f.write(f"================================================================================\n\n")
    except Exception as e:
        logger.error(f"Failed to log prompt: {str(e)}")
