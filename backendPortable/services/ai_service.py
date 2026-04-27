"""
services/ai_service.py – AI service integration for quiz generation.
"""

import logging
from typing import List, Dict, Any

import httpx
from config import settings

logger = logging.getLogger(__name__)


async def generate_questions_from_text(
    text: str,
    total_questions: int,
    mc_ratio: float,
    difficulty: str
) -> List[Dict[str, Any]]:
    """
    Generate quiz questions from text using Gemini AI.
    
    Args:
        text: Source text for question generation
        total_questions: Number of questions to generate
        mc_ratio: Ratio of multiple choice questions (0.0-1.0)
        difficulty: Question difficulty level
        
    Returns:
        List of question dictionaries
    """
    try:
        if not settings.GEMINI_API_KEY:
            raise ValueError("Gemini API key not configured")
        
        # Calculate number of multiple choice and open-ended questions
        mc_count = int(total_questions * mc_ratio)
        oe_count = total_questions - mc_count
        
        # Build prompt
        prompt = _build_quiz_prompt(text, mc_count, oe_count, difficulty)
        
        # Call Gemini API
        questions = await _call_gemini_api(prompt)
        
        # Validate and format questions
        formatted_questions = _format_questions(questions, mc_count, oe_count)
        
        logger.info(f"Generated {len(formatted_questions)} questions from text")
        return formatted_questions
        
    except Exception as e:
        logger.error(f"Error generating questions: {str(e)}")
        raise ValueError("Failed to generate questions from text")


def _build_quiz_prompt(text: str, mc_count: int, oe_count: int, difficulty: str) -> str:
    """Build the prompt for Gemini AI."""
    prompt = f"""
Generate a quiz based on the following text. The quiz should contain {mc_count} multiple choice questions and {oe_count} open-ended questions.
All questions should be {difficulty} difficulty level.

Text:
{text}

Please generate the questions in the following JSON format:
[
    {{
        "type": "multiple_choice",
        "text": "Question text here",
        "options": {{"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}},
        "correct_answer": "A",
        "topic": "Topic name",
        "difficulty": "{difficulty}"
    }},
    {{
        "type": "open_ended",
        "text": "Question text here",
        "topic": "Topic name",
        "difficulty": "{difficulty}",
        "rubric": "Scoring criteria for this question"
    }}
]

Make sure the questions are relevant to the text and test understanding of key concepts.
"""
    return prompt


async def _call_gemini_api(prompt: str) -> List[Dict[str, Any]]:
    """Call Gemini API to generate questions."""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent"
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": settings.GEMINI_API_KEY
        }
        
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 8192,
                "responseMimeType": "application/json",
            }
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract generated text
            if "candidates" not in result or not result["candidates"]:
                raise ValueError("No response from Gemini API")
            
            generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
            
            # Parse JSON response
            import json
            try:
                questions = json.loads(generated_text)
                return questions if isinstance(questions, list) else []
            except json.JSONDecodeError:
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'\[.*\]', generated_text, re.DOTALL)
                if json_match:
                    questions = json.loads(json_match.group())
                    return questions if isinstance(questions, list) else []
                else:
                    raise ValueError("Could not parse JSON response from Gemini")
                    
    except httpx.HTTPStatusError as e:
        logger.error(f"Gemini API error: {e.response.status_code} - {e.response.text}")
        raise ValueError("Failed to call Gemini API")
    except Exception as e:
        logger.error(f"Error calling Gemini API: {str(e)}")
        raise ValueError("Failed to generate questions")


def _format_questions(questions: List[Dict[str, Any]], mc_count: int, oe_count: int) -> List[Dict[str, Any]]:
    """Validate and format generated questions."""
    formatted = []
    
    for i, q in enumerate(questions):
        try:
            # Validate required fields
            if not all(key in q for key in ["type", "text", "topic", "difficulty"]):
                logger.warning(f"Skipping question {i} - missing required fields")
                continue
            
            # Validate question type
            if q["type"] not in ["multiple_choice", "open_ended"]:
                logger.warning(f"Skipping question {i} - invalid type: {q['type']}")
                continue
            
            # Type-specific validation
            if q["type"] == "multiple_choice":
                if not all(key in q for key in ["options", "correct_answer"]):
                    logger.warning(f"Skipping MC question {i} - missing options or correct_answer")
                    continue
                
                if not isinstance(q["options"], dict) or len(q["options"]) != 4:
                    logger.warning(f"Skipping MC question {i} - invalid options format")
                    continue
                
                if q["correct_answer"] not in q["options"]:
                    logger.warning(f"Skipping MC question {i} - correct_answer not in options")
                    continue
            
            # Add the question to formatted list
            formatted.append(q)
            
        except Exception as e:
            logger.warning(f"Error formatting question {i}: {str(e)}")
            continue
    
    # Ensure we have the right number of questions
    if len(formatted) < (mc_count + oe_count):
        logger.warning(f"Generated {len(formatted)} questions, expected {mc_count + oe_count}")
    
    return formatted[: (mc_count + oe_count)]
