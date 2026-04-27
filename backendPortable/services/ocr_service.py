"""
services/ocr_service.py - OCR service used by background note processing.

This module is intentionally lightweight and uses lazy imports so that
backend startup does not fail even if optional OCR dependencies are missing.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Literal

from config import settings

logger = logging.getLogger(__name__)


OCRStrategy = Literal["tesseract_gemini", "tesseract_only", "gemini_direct"]


def _enhance_for_ocr(image):
    """Simple preprocessing: grayscale + contrast boost."""
    # Local import keeps module import safe if Pillow is missing.
    from PIL import ImageEnhance

    gray = image.convert("L")
    gray = ImageEnhance.Contrast(gray).enhance(2.0)
    gray = ImageEnhance.Sharpness(gray).enhance(1.5)
    return gray


def _read_text_file(file_path: str) -> str:
    return Path(file_path).read_text(encoding="utf-8", errors="replace")


def _run_tesseract(image, lang: str = "tur+eng") -> str:
    # Local import keeps module import safe if pytesseract is missing.
    try:
        import pytesseract
    except Exception as e:
        raise ValueError(f"Tesseract OCR requires `pytesseract` dependency: {e}") from e

    processed = _enhance_for_ocr(image)
    return pytesseract.image_to_string(processed, lang=lang)


async def _gemini_cleanup(raw_text: str) -> str:
    """
    Optional cleanup step. If Gemini dependencies are not available or API key
    is missing, returns the original text.
    """
    if not settings.GEMINI_API_KEY:
        return raw_text

    try:
        import google.generativeai as genai
    except Exception as e:
        logger.warning(f"Gemini cleanup skipped (dependency missing): {e}")
        return raw_text

    prompt = (
        "Aşağıdaki metin bir OCR çıktısıdır. Gereksiz boşlukları, sayfa "
        "numaralarını ve OCR hatalarını temizle. Anlam ve yapıyı koru. "
        "Yalnızca temizlenmiş metni döndür, açıklama ekleme.\n\n"
        f"---\n{raw_text}\n---"
    )

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.GEMINI_MODEL)

    # Some SDK versions expose async helpers, others don't. Support both.
    try:
        response = await model.generate_content_async(prompt)
    except AttributeError:
        response = await asyncio.to_thread(model.generate_content, prompt)

    return (response.text or "").strip() or raw_text


async def _extract_from_pdf_pages(pdf_bytes: bytes, strategy: OCRStrategy) -> str:
    # Local import keeps module import safe if PyMuPDF is missing.
    try:
        import fitz  # PyMuPDF
    except Exception as e:
        raise ValueError(f"PDF OCR requires PyMuPDF (fitz) dependency: {e}") from e

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_texts: list[str] = []

    for page in doc:
        # Render page to an image at a reasonable DPI.
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")

        # Decode to PIL image for Tesseract.
        from PIL import Image

        image = Image.open(io_bytes_to_stream(img_bytes))

        if strategy in ("tesseract_gemini", "tesseract_only"):
            page_texts.append(_run_tesseract(image))
        elif strategy == "gemini_direct":
            page_texts.append(await _extract_from_gemini_image(image))
        else:
            page_texts.append(_run_tesseract(image))

    raw_text = "\n\n--- SAYFA SONU ---\n\n".join(t for t in page_texts if t is not None)
    return raw_text


def io_bytes_to_stream(img_bytes: bytes):
    """Small helper to avoid repeating BytesIO import in multiple branches."""
    import io

    return io.BytesIO(img_bytes)


async def _extract_from_gemini_image(image) -> str:
    """Best-effort Gemini multimodal extraction. Falls back to empty on failure."""
    if not settings.GEMINI_API_KEY:
        raise ValueError("Gemini extraction requested but GEMINI_API_KEY is not set.")

    try:
        import google.generativeai as genai
    except Exception as e:
        raise ValueError(f"Gemini OCR requires google-generativeai dependency: {e}") from e

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.GEMINI_MODEL)

    prompt = "Bu görseldeki tüm metni çıkar. Yalnızca metni döndür, açıklama ekleme."

    try:
        response = await model.generate_content_async([prompt, image])
    except AttributeError:
        response = await asyncio.to_thread(model.generate_content, [prompt, image])

    return (response.text or "").strip()


async def extract_text_from_file(
    file_path: str,
    file_type: str,
    strategy: OCRStrategy = "tesseract_gemini",
) -> str:
    """
    Extract raw OCR text from an uploaded file.

    Signature is compatible with `backendWindsurf2/services/celery_tasks.py`:
    it calls `await extract_text_from_file(file_path, file_type)`.

    Returns:
        Raw OCR text (cleaning, if enabled, happens via Gemini cleanup).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found for OCR: {file_path}")

    raw_text: str = ""

    # Read bytes once.
    file_bytes = path.read_bytes()

    file_type_norm = (file_type or "").lower().strip()
    if file_type_norm == "pdf":
        raw_text = await _extract_from_pdf_pages(file_bytes, strategy=strategy)
    elif file_type_norm in ("image", "jpg", "jpeg", "png"):
        from PIL import Image

        image = Image.open(io_bytes_to_stream(file_bytes))
        image.load()

        if strategy in ("tesseract_gemini", "tesseract_only"):
            raw_text = _run_tesseract(image)
        elif strategy == "gemini_direct":
            raw_text = await _extract_from_gemini_image(image)
        else:
            raw_text = _run_tesseract(image)
    elif file_type_norm in ("text", "txt"):
        raw_text = _read_text_file(str(path))
    else:
        # Unknown type: best-effort treat as text.
        raw_text = file_bytes.decode("utf-8", errors="replace")

    raw_text = (raw_text or "").strip()
    if not raw_text:
        return ""

    # Optional cleanup step (kept separate from celery's clean_text()).
    if strategy == "tesseract_gemini":
        try:
            cleaned = await _gemini_cleanup(raw_text)
            return cleaned.strip() or raw_text
        except Exception as e:
            logger.warning(f"Gemini cleanup failed, returning raw OCR: {e}")
            return raw_text

    return raw_text

