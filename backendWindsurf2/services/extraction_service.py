"""
services/extraction_service.py – Modüler metin çıkarma (extraction) servisi.

Desteklenen formatlar:
  - .txt   → doğrudan UTF-8 okuma
  - .pdf   → PyMuPDF (fitz) ile sayfa sayfa metin çıkarma
  - .docx  → python-docx ile paragraf okuma
  - .jpg / .jpeg / .png  → Pillow + pytesseract OCR
                            (öncesinde OpenCV ile gürültü azaltma / kontrast iyileştirme)

Her fonksiyon saf (pure) & bağımsız tutulmuştur; router veya Celery
görevleri istedikleri yöntemi doğrudan çağırabilir.
"""

from __future__ import annotations

import asyncio
import base64
import io
import logging
import re

import httpx

from config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Geçerli uzantılar (doğrulama için merkezi bir yer)
# ---------------------------------------------------------------------------
ALLOWED_EXTENSIONS: frozenset[str] = frozenset(
    {".pdf", ".jpeg", ".jpg", ".png", ".docx", ".txt"}
)


# ---------------------------------------------------------------------------
# Yardımcı: basit metin temizleme
# ---------------------------------------------------------------------------
def clean_text(raw: str) -> str:
    """
    Ham metinden fazladan boşlukları, art arda gelen boş satırları ve
    satır başı/sonu boşluklarını temizler.
    """
    if not raw:
        return ""
    # Satır başı + sonu boşlukları kaldır
    lines = [line.strip() for line in raw.splitlines()]
    # 3'ten fazla ardışık boş satırı 2'ye indir
    cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
    return cleaned.strip()


# ---------------------------------------------------------------------------
# .txt dosyaları
# ---------------------------------------------------------------------------
def extract_from_txt(file_bytes: bytes) -> str:
    """UTF-8 (hatalı karakterler 'replace' ile) decode ederek okur."""
    return file_bytes.decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# .pdf dosyaları – PyMuPDF (fitz)
# ---------------------------------------------------------------------------
def extract_from_pdf(file_bytes: bytes) -> str:
    """
    PyMuPDF kullanarak her sayfanın metnini çıkarır.
    OCR (Tesseract) devre dışı bırakılmıştır.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise ImportError(
            "PDF desteği için 'PyMuPDF' gereklidir."
        ) from exc

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    page_texts: list[str] = []

    for page in doc:
        text = page.get_text("text").strip()
        if text:
            page_texts.append(text)

    doc.close()
    return "\n\n".join(page_texts)


def _render_pdf_pages(file_bytes: bytes, max_pages: int = 20) -> list[tuple[int, bytes]]:
    """Render PDF pages to PNG bytes for AI vision fallback."""
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise ImportError("PDF gorsel isleme icin 'PyMuPDF' gereklidir.") from exc

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    rendered: list[tuple[int, bytes]] = []
    matrix = fitz.Matrix(1.7, 1.7)

    try:
        for page_index in range(min(doc.page_count, max_pages)):
            page = doc.load_page(page_index)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            rendered.append((page_index + 1, pix.tobytes("png")))
    finally:
        doc.close()

    return rendered


async def _extract_text_from_image_with_gemini(
    image_bytes: bytes,
    mime_type: str,
    page_label: str = "dosya",
) -> str:
    """Use Gemini Vision through REST inline_data to extract text from an image."""
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY ayarli olmadigi icin gorsel metin cikarilamadi")

    model_name = settings.GEMINI_MODEL.strip() or "gemini-1.5-flash"
    if model_name.startswith("models/"):
        model_name = model_name.removeprefix("models/")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "Bu ders notu gorselindeki okunabilir tum metni cikar. "
                            "Basliklari, maddeleri, tablo satirlarini ve formulleri mumkun oldugunca koru. "
                            "Yalnizca cikarilan metni dondur; aciklama ekleme. "
                            "Okunabilir metin yoksa sadece EMPTY_PAGE yaz."
                        )
                    },
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": base64.b64encode(image_bytes).decode("ascii"),
                        }
                    },
                ],
            }
        ],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 4096},
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(url, params={"key": settings.GEMINI_API_KEY}, json=payload)
        response.raise_for_status()
        data = response.json()

    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text = "\n".join(part.get("text", "") for part in parts).strip()
    logger.info("Gemini vision extraction completed | page=%s | chars=%d", page_label, len(text))
    return "" if text == "EMPTY_PAGE" else text


async def extract_pdf_with_gemini_vision(file_bytes: bytes) -> str:
    """Fallback for scanned/image-only PDFs."""
    rendered_pages = await asyncio.to_thread(_render_pdf_pages, file_bytes)
    page_texts: list[str] = []

    for page_number, png_bytes in rendered_pages:
        try:
            text = await _extract_text_from_image_with_gemini(
                png_bytes,
                "image/png",
                page_label=f"pdf-page-{page_number}",
            )
            if text.strip():
                page_texts.append(f"--- Sayfa {page_number} ---\n{text.strip()}")
        except Exception as exc:
            logger.warning("Gemini PDF page extraction failed | page=%s | error=%s", page_number, exc)

    return "\n\n".join(page_texts)


# ---------------------------------------------------------------------------
# .docx dosyaları – python-docx
# ---------------------------------------------------------------------------
def extract_from_docx(file_bytes: bytes) -> str:
    """
    python-docx kullanarak tüm paragrafları okur.
    Tablolardaki hücreler de dahil edilir.
    """
    try:
        from docx import Document
    except ImportError as exc:
        raise ImportError(
            "DOCX desteği için 'python-docx' gereklidir."
        ) from exc

    doc = Document(io.BytesIO(file_bytes))
    parts: list[str] = []

    # Paragraflar
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            parts.append(text)

    # Tablolar
    for table in doc.tables:
        for row in table.rows:
            row_texts = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_texts:
                parts.append(" | ".join(row_texts))

    return "\n".join(parts)


async def extract_from_image(file_bytes: bytes, extension: str) -> str:
    """Extract text from JPG/PNG files with Gemini Vision."""
    mime_type = "image/png" if extension == ".png" else "image/jpeg"
    return await _extract_text_from_image_with_gemini(file_bytes, mime_type)


# ---------------------------------------------------------------------------
# Ana dağıtıcı (dispatcher) – async wrapper
# ---------------------------------------------------------------------------
async def extract_text(file_bytes: bytes, extension: str) -> tuple[str, str]:
    """
    Dosya uzantısına göre uygun çıkarma fonksiyonunu çağırır.

    Args:
        file_bytes: Yüklenen dosyanın ham byte içeriği.
        extension:  Küçük harfe indirgenmiş uzantı, örn. '.pdf', '.txt'.

    Returns:
        (raw_text, cleaned_text) çifti.

    Raises:
        ValueError: Desteklenmeyen dosya uzantısı.
    """
    ext = extension.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Desteklenmeyen dosya uzantısı: '{ext}'. "
            f"Kabul edilenler: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # CPU-yoğun işlemler asyncio event loop'u bloke etmemeli
    if ext == ".txt":
        raw = await asyncio.to_thread(extract_from_txt, file_bytes)
    elif ext == ".pdf":
        raw = await asyncio.to_thread(extract_from_pdf, file_bytes)
        if not clean_text(raw):
            logger.info("PDF embedded text is empty; trying Gemini vision fallback.")
            raw = await extract_pdf_with_gemini_vision(file_bytes)
    elif ext == ".docx":
        raw = await asyncio.to_thread(extract_from_docx, file_bytes)
    elif ext in (".jpg", ".jpeg", ".png"):
        raw = await extract_from_image(file_bytes, ext)
    else:
        # Bu noktaya yukarıdaki kontrol sonrası ulaşılamaz; güvenlik ağı.
        raise ValueError(f"Beklenmeyen uzantı: '{ext}'")

    cleaned = clean_text(raw)
    return raw, cleaned
