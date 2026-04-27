"""
utils/localization.py – Helper for localizing quiz feedback strings.
"""

def get_localized_feedback(language: str, score: float, correct_answer: str) -> str:
    """Returns localized feedback for test questions."""
    is_correct = score > 0
    
    if language == 'tr':
        return "Doğru!" if is_correct else f"Yanlış. Doğru cevap: {correct_answer}."
    elif language == 'en':
        return "Correct!" if is_correct else f"Incorrect. The correct answer is {correct_answer}."
    else:
        # Fallback to English if unknown language
        return "Correct!" if is_correct else f"Incorrect. The correct answer is {correct_answer}."
