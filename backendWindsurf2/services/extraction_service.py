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
import io
import logging
import re
import shutil
from pathlib import Path
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


def extract_from_image(file_bytes: bytes, lang: str = "tur+eng") -> str:
    """OCR devre dışı bırakıldığı için boş metin döner."""
    logger.warning("OCR is disabled. Image extraction skipped.")
    return "Görselden metin çıkarma (OCR) devre dışı bırakılmıştır."


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
    elif ext == ".docx":
        raw = await asyncio.to_thread(extract_from_docx, file_bytes)
    elif ext in (".jpg", ".jpeg", ".png"):
        raw = await asyncio.to_thread(extract_from_image, file_bytes)
    else:
        # Bu noktaya yukarıdaki kontrol sonrası ulaşılamaz; güvenlik ağı.
        raise ValueError(f"Beklenmeyen uzantı: '{ext}'")

    cleaned = clean_text(raw)
    return raw, cleaned
