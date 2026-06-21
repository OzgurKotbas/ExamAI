"""
routers/notes.py – Not yükleme endpoint'i.

POST /api/v1/notes
  - JWT (Bearer token) ile yetkilendirme gerektirir.
  - Desteklenen formatlar: .pdf, .jpeg, .jpg, .png, .docx, .txt
  - Metin çıkarma işlemleri services/extraction_service.py üzerinden yapılır.
  - Çıkarılan metin Note tablosuna kaydedilir.

Yanıt örneği:
  {"message": "Note uploaded successfully", "note_id": "<uuid>"}
"""

from __future__ import annotations

from typing import List
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.note import Note
from models.user import User
from services.auth_service import get_current_user
from services.extraction_service import ALLOWED_EXTENSIONS, extract_text
from utils.security import encrypt_text
from utils.i18n import translate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notes", tags=["Notes"])

# Maksimum izin verilen dosya boyutu: 20 MB
MAX_FILE_SIZE_BYTES: int = 20 * 1024 * 1024


# ---------------------------------------------------------------------------
# Yardımcı: uzantı doğrulama
# ---------------------------------------------------------------------------
def _validate_extension(filename: str | None, lang: str = "tr") -> str:
    """
    Dosya adından uzantıyı çıkarır ve izin verilenler listesiyle karşılaştırır.
    Geçersiz uzantıda HTTP 400 fırlatır.

    Returns:
        Küçük harfli uzantı, örn. '.pdf'.
    """
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=translate("UNSUPPORTED_FORMAT", lang),
        )

    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{translate('UNSUPPORTED_FORMAT', lang)}: '{ext}'",
        )
    return ext


def _map_ext_to_file_type(ext: str) -> str:
    """Uzantıyı Note.file_type değerine eşler."""
    _map = {
        ".pdf": "pdf",
        ".txt": "text",
        ".docx": "docx",
        ".jpg": "image",
        ".jpeg": "image",
        ".png": "image",
    }
    return _map.get(ext, "unknown")


# ---------------------------------------------------------------------------
# POST /api/v1/notes
# ---------------------------------------------------------------------------
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Not yükle - Tek veya Çoklu (PDF / DOCX / TXT / Görsel)",
    description=(
        "Kullanıcının ders notlarını yükler, metni çıkarır ve veritabanına kaydeder. "
        "Tek veya çoklu dosya (max 10) yüklenebilir. "
        "Desteklenen formatlar: .pdf, .docx, .txt, .jpg, .jpeg, .png"
    ),
    responses={
        201: {
            "description": "Notlar başarıyla yüklendi",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Notlar başarıyla yüklendi",
                        "notes": [
                            {"note_id": "uuid-1", "filename": "file1.pdf"},
                            {"note_id": "uuid-2", "filename": "file2.docx"},
                        ],
                        "total": 2,
                    }
                }
            },
        },
        400: {"description": "Geçersiz dosya formatı veya içerik hatası"},
        401: {"description": "Yetkilendirme başarısız"},
        413: {"description": "Dosya boyutu çok büyük"},
        500: {"description": "Sunucu hatası"},
    },
)
async def upload_notes(
    files: List[UploadFile] = File(..., description="Yüklenecek not dosyaları (max 10)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lang: str = Header("tr", alias="X-Language")
):
    """
    Çoklu not dosyalarını yükle, metni çıkar ve kaydet.

    - **files**: Yüklenecek dosyalar (.pdf, .docx, .txt, .jpg, .jpeg, .png)
    - **Authorization**: Bearer <JWT token> (header'da zorunlu)
    - **Max files**: 10 adet
    - **Max size**: Her dosya 20MB
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=translate("MAX_FILES_EXCEEDED", lang),
        )

    uploaded_notes = []
    errors = []

    for file in files:
        try:
            # 1. Uzantı doğrulama
            ext = _validate_extension(file.filename, lang=lang)
            file_type = _map_ext_to_file_type(ext)

            logger.info(
                "Not yükleme başladı | user_id=%s | dosya=%s | tip=%s",
                current_user.id,
                file.filename,
                file_type,
            )

            # 2. Dosya içeriğini oku ve boyut kontrolü yap
            try:
                file_bytes = await file.read()
            except Exception as exc:
                logger.error("Dosya okunurken hata: %s", exc)
                errors.append({"filename": file.filename, "error": "Dosya okunurken hata oluştu"})
                continue
            finally:
                await file.close()

            if len(file_bytes) == 0:
                errors.append({"filename": file.filename, "error": "Dosya boş"})
                continue

            if len(file_bytes) > MAX_FILE_SIZE_BYTES:
                errors.append({"filename": file.filename, "error": f"Dosya boyutu {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB'ı aşıyor"})
                continue

            # 3. Metin çıkarma
            try:
                raw_text, cleaned_text = await extract_text(file_bytes, ext)
            except Exception as exc:
                logger.error("Metin çıkarma hatası (%s): %s", file.filename, exc)
                errors.append({"filename": file.filename, "error": "Metin çıkarılamadı"})
                continue

            if not raw_text.strip():
                errors.append({"filename": file.filename, "error": "Dosyadan metin çıkarılamadı"})
                continue

            # 4. Veritabanına kaydet
            context_id = str(uuid.uuid4())

            # AES-256-GCM şifreleme
            try:
                raw_text_enc = encrypt_text(raw_text)
                cleaned_text_enc = encrypt_text(cleaned_text)
            except Exception as exc:
                logger.error("Metin şifreleme hatası (%s): %s", file.filename, exc)
                errors.append({"filename": file.filename, "error": "Şifreleme hatası"})
                continue

            note = Note(
                user_id=current_user.id,
                context_id=context_id,
                original_filename=file.filename or "unnamed",
                file_type=file_type,
                raw_text_encrypted=raw_text_enc,
                cleaned_text_encrypted=cleaned_text_enc,
            )

            db.add(note)
            await db.flush()
            note_id = str(note.id)

            logger.info(
                "Not kaydedildi | note_id=%s | user_id=%s | char_count=%d",
                note_id,
                current_user.id,
                len(raw_text),
            )

            uploaded_notes.append({
                "id": note_id,
                "note_id": note_id,
                "filename": file.filename,
                "original_filename": file.filename,
            })

        except Exception as exc:
            logger.error("Dosya işleme hatası (%s): %s", file.filename, exc)
            errors.append({"filename": file.filename or "unknown", "error": str(exc)})
            continue

    # Commit all successful notes
    if uploaded_notes:
        await db.commit()

    # Eğer hiçbir dosya yüklenemediyse hata dön
    if not uploaded_notes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": translate("INTERNAL_SERVER_ERROR", lang), "errors": errors},
        )

    return {
        "message": f"{len(uploaded_notes)} {translate('UPLOAD_SUCCESS', lang)}",
        "notes": uploaded_notes,
        "total": len(uploaded_notes),
        "errors": errors if errors else None,
    }


# ---------------------------------------------------------------------------
# GET /api/v1/notes  (opsiyonel – kullanıcının notlarını listele)
# ---------------------------------------------------------------------------
@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Kullanıcıya ait notları listele",
)
async def list_notes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lang: str = Header("tr", alias="X-Language")
):
    """Giriş yapmış kullanıcının tüm notlarını döndürür."""
    from sqlalchemy import select

    result = await db.execute(
        select(Note)
        .where(Note.user_id == current_user.id)
        .order_by(Note.created_at.desc())
    )
    notes = result.scalars().all()

    return {
        "notes": [
            {
                "note_id": str(n.id),
                "id": str(n.id),
                "context_id": n.context_id,
                "filename": n.original_filename,
                "original_filename": n.original_filename,
                "file_type": n.file_type,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notes
        ],
        "total": len(notes),
    }


# ---------------------------------------------------------------------------
# DELETE /api/v1/notes/{note_id}
# ---------------------------------------------------------------------------
@router.delete(
    "/{note_id}",
    status_code=status.HTTP_200_OK,
    summary="Not sil",
    description="Belirtilen notu ve ona bağlı tüm sınavları siler.",
)
async def delete_note(
    note_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    lang: str = Header("tr", alias="X-Language")
):
    """
    Kullanıcının bir notunu siler. Cascade sayesinde bağlı sınavlar da silinir.
    """
    from sqlalchemy import select

    # Notu bul ve sahiplik kontrolü yap
    result = await db.execute(
        select(Note).where(Note.id == note_id, Note.user_id == current_user.id)
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=translate("RESOURCE_NOT_FOUND", lang),
        )

    # Sil
    await db.delete(note)
    await db.commit()

    logger.info("Not silindi | note_id=%s | user_id=%s", note_id, current_user.id)

    return {"message": translate("DELETE_SUCCESS", lang)}
