"""
utils/localization.py – Helper for localizing quiz feedback strings.
"""

def get_localized_feedback(language: str, score: float, correct_answer: str, options: dict = None) -> str:
    """Returns localized feedback for test questions."""
    is_correct = score > 0
    
    # Get option text if available (e.g. "D) 1993")
    answer_display = correct_answer
    if options and correct_answer in options:
        answer_display = f"{correct_answer}) {options[correct_answer]}"
    
    if language == 'tr':
        return "Doğru!" if is_correct else f"Yanlış. Doğru cevap: {answer_display}."
    elif language == 'en':
        return "Correct!" if is_correct else f"Incorrect. The correct answer is {answer_display}."
    else:
        # Fallback to English if unknown language
        return "Correct!" if is_correct else f"Incorrect. The correct answer is {answer_display}."
