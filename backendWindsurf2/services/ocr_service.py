"""
services/ocr_service.py - OCR service used by background note processing.

This module is intentionally lightweight and uses lazy imports so that
backend startup does not fail even if optional OCR dependencies are missing.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
from pathlib import Path
from typing import Literal

from config import settings

logger = logging.getLogger(__name__)


OCRStrategy = Literal["tesseract_gemini", "tesseract_only", "gemini_direct"]


def _enhance_for_ocr(image):
    """
    Enhanced image preprocessing for OCR accuracy:
    1. Convert to grayscale
    2. Apply CLAHE contrast enhancement (OpenCV) or PIL fallback
    3. Apply Gaussian noise reduction
    4. Apply adaptive thresholding for better text detection
    Falls back to PIL if OpenCV is unavailable.
    """
    try:
        import cv2
        import numpy as np
        from PIL import Image as PILImage
        import io

        # Convert PIL image to OpenCV format
        pil_img = image.convert("L")  # Grayscale
        cv_img = np.array(pil_img)

        # 1. CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cv_img = clahe.apply(cv_img)

        # 2. Gaussian blur for noise reduction
        cv_img = cv2.GaussianBlur(cv_img, (3, 3), 0)

        # 3. Adaptive thresholding for better binarization
        cv_img = cv2.adaptiveThreshold(
            cv_img, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )

        # Convert back to PIL image
        return PILImage.fromarray(cv_img)

    except ImportError:
        logger.info("OpenCV not available, using PIL for image enhancement (fallback)")
        # PIL fallback: grayscale + contrast + sharpness boost
        from PIL import ImageEnhance
        gray = image.convert("L")
        gray = ImageEnhance.Contrast(gray).enhance(2.0)
        gray = ImageEnhance.Sharpness(gray).enhance(1.5)
        return gray
    except Exception as e:
        logger.warning(f"Image enhancement failed: {e}. Using original image.")
        return image.convert("L")


def _read_text_file(file_path: str) -> str:
    return Path(file_path).read_text(encoding="utf-8", errors="replace")


def _run_tesseract(image, lang: str = "tur+eng") -> str:
    # Local import keeps module import safe if pytesseract is missing.
    try:
        import pytesseract
        
        # Determine dynamic path or use config
        tess_cmd = settings.TESSERACT_CMD_PATH or shutil.which("tesseract")
        if tess_cmd:
            pytesseract.pytesseract.tesseract_cmd = tess_cmd
        else:
            logger.warning("tesseract executable not found in PATH and TESSERACT_CMD_PATH not set. OCR might fail on Windows if not configured.")
            
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
        raise ValueError(f"PDF extraction requires PyMuPDF (fitz) dependency: {e}") from e

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_texts: list[str] = []

    for page in doc:
        # OCR is discarded by user choice. We only extract embedded text.
        text = page.get_text("text").strip()
        if text:
            page_texts.append(text)
    
    doc.close()
    raw_text = "\n\n".join(t for t in page_texts if t is not None)
    return raw_text


def io_bytes_to_stream(img_bytes: bytes):
    """Small helper to avoid repeating BytesIO import in multiple branches."""
    import io
    return io.BytesIO(img_bytes)


async def _extract_from_gemini_image(image) -> str:
    """Gemini extraction disabled as per user request (OCR vazgeç)."""
    logger.info("Gemini image extraction skipped (OCR disabled by user)")
    return ""


async def extract_text_from_file(
    file_path: str,
    file_type: str,
    strategy: OCRStrategy = "tesseract_gemini",
) -> str:
    """
    Extract text from an uploaded file WITHOUT OCR.
    
    Supported: PDF (embedded text only), TXT.
    Images will return an empty string/message because OCR is discarded.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    raw_text: str = ""
    file_bytes = path.read_bytes()
    file_type_norm = (file_type or "").lower().strip()

    if file_type_norm == "pdf":
        raw_text = await _extract_from_pdf_pages(file_bytes, strategy=strategy)
    elif file_type_norm in ("text", "txt"):
        raw_text = _read_text_file(str(path))
    elif file_type_norm in ("image", "jpg", "jpeg", "png"):
        logger.warning("OCR is disabled. Image processing is skipped.")
        return "Görsel dosyaları işleme (OCR) devre dışı bırakılmıştır. Lütfen metin tabanlı PDF veya TXT dosyası yükleyin."
    else:
        # Unknown type: best-effort treat as text.
        try:
            raw_text = file_bytes.decode("utf-8", errors="replace")
        except:
            raw_text = ""

    return (raw_text or "").strip()

