# ExamAI – Not Yükleme Modülü: Teknik Dokümantasyon

**Tarih:** 2026-04-01  
**Versiyon:** 1.0.0  
**İlgili dosyalar:** `routers/notes.py`, `services/extraction_service.py`, `requirements.txt`, `main.py`

---

## 1. Genel Bakış

Bu rapor, ExamAI backend'ine eklenen **not yükleme (note upload) modülünün** teknik detaylarını açıklar.
Modül; kullanıcıların `.pdf`, `.docx`, `.txt`, `.jpg`, `.jpeg` ve `.png` formatındaki ders notlarını yükleyebilmesini,
içlerindeki metnin otomatik çıkarılmasını ve veritabanına kaydedilmesini sağlar.

---

## 2. Eklenen / Değiştirilen Dosyalar

| Dosya | İşlem | Açıklama |
|---|---|---|
| `services/extraction_service.py` | **YENİ OLUŞTURULDU** | Format bazında metin çıkarma servisi |
| `routers/notes.py` | **YENİ OLUŞTURULDU** | Not yükleme ve listeleme endpoint'leri |
| `requirements.txt` | **GÜNCELLENDİ** | Yeni Python bağımlılıkları eklendi |
| `main.py` | **DEĞİŞİKLİK GEREKMEDİ** | Router kaydı zaten mevcuttu |

---

## 3. API Endpoint Detayları

### `POST /api/v1/notes`

| Özellik | Değer |
|---|---|
| **URL** | `POST /api/v1/notes` |
| **Yetkilendirme** | `Authorization: Bearer <JWT>` (zorunlu) |
| **İstek tipi** | `multipart/form-data` |
| **Form alanı** | `file: UploadFile` |
| **Maks. dosya boyutu** | 20 MB |

**Başarılı yanıt (HTTP 201):**
```json
{
  "message": "Note uploaded successfully",
  "note_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

**Hata yanıtları:**

| HTTP Kodu | Durum | Açıklama |
|---|---|---|
| `400` | Bad Request | Geçersiz dosya uzantısı veya boş dosya |
| `400` | Bad Request | Dosyadan metin çıkarılamadı |
| `401` | Unauthorized | JWT token eksik veya geçersiz |
| `413` | Payload Too Large | Dosya boyutu 20 MB'ı aşıyor |
| `500` | Internal Server Error | Sunucu veya DB hatası |

---

### `GET /api/v1/notes`

Giriş yapmış kullanıcının tüm notlarını listeler. Yetkilendirme gerektirir.

**Başarılı yanıt (HTTP 200):**
```json
{
  "notes": [
    {
      "note_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "context_id": "7e4a6c9d-...",
      "original_filename": "ders_notu.pdf",
      "file_type": "pdf",
      "created_at": "2026-04-01T12:00:00+00:00"
    }
  ],
  "total": 1
}
```

---

## 4. Mimari: `services/extraction_service.py`

Modüler tasarım gereği **metin çıkarma işlemleri router'dan ayrılmıştır**.

```
routers/notes.py
    └─► services/extraction_service.py
            ├── extract_from_txt()   → UTF-8 decode
            ├── extract_from_pdf()   → PyMuPDF (fitz) + OCR fallback
            ├── extract_from_docx()  → python-docx (paragraf + tablo)
            ├── extract_from_image() → OpenCV ön işleme + pytesseract
            └── extract_text()       → async dispatcher (ana giriş noktası)
```

### 4.1. Desteklenen Formatlar ve Yöntemler

| Format | Uzantı(lar) | Yöntem | Kütüphane |
|---|---|---|---|
| Düz metin | `.txt` | UTF-8 decode | Built-in |
| PDF belgesi | `.pdf` | Gömülü metin; yoksa render+OCR | PyMuPDF (`fitz`) |
| Word belgesi | `.docx` | Paragraf + tablo okuma | python-docx |
| Görsel (OCR) | `.jpg`, `.jpeg`, `.png` | OpenCV ön işleme → Tesseract | opencv-python, pytesseract |

### 4.2. Görsel Ön İşleme Pipeline'ı (OCR Kalite İyileştirme)

```
Ham görsel (bytes)
    │
    ▼
cv2.imdecode() ──→ BGR görsel
    │
    ▼
cvtColor(BGR→GRAY) ──→ Gri tonlamalı
    │
    ▼
CLAHE (clipLimit=2.0) ──→ Kontrast iyileştirilmiş
    │
    ▼
GaussianBlur (3×3) ──→ Gürültü azaltılmış
    │
    ▼
Otsu Eşikleme ──→ İkili (siyah/beyaz) görsel
    │
    ▼
pytesseract.image_to_string(lang="tur+eng")
    │
    ▼
Ham OCR metni
```

> **Not:** `opencv-python` kurulu değilse servis, Pillow tabanlı basit kontrast artışına düşer ve uyarı loglar.

### 4.3. `clean_text()` Fonksiyonu

- Satır başı/sonu boşluklarını (`strip`) kaldırır  
- 3'ten fazla ardışık boş satırı 2'ye indirir  
- `cleaned_text_encrypted` alanına yazılan değer bu fonksiyondan geçirilmiş metindir

---

## 5. Veritabanı Şeması (Mevcut `Note` Modeli)

```python
class Note(Base):
    __tablename__ = "notes"

    id: UUID                    # Primary key (uuid4)
    user_id: UUID               # FK → users.id (CASCADE DELETE)
    context_id: str             # Benzersiz context tanımlayıcı (uuid4)
    original_filename: str      # Yüklenen dosyanın adı
    file_type: str              # "pdf" | "text" | "docx" | "image"
    raw_text_encrypted: str     # Çıkarılan ham metin
    cleaned_text_encrypted: str # Temizlenmiş metin
    ocr_quality_score: float    # 0-1 (isteğe bağlı, ileride doldurulabilir)
    created_at: datetime        # Oluşturulma zamanı (server_default=now())
```

> **Önemli:** Mevcut model alanları `_encrypted` sonekiyle bittiğinden, üretim ortamında `utils/security.py` üzerinden AES-256-GCM şifreleme katmanı etkinleştirilmelidir.

---

## 6. `main.py` – Router Kaydı

`main.py` incelendiğinde router kaydının **zaten mevcut** olduğu görülmüştür:

```python
from routers import auth, quiz, notes          # satır 17

app.include_router(notes.router, prefix="/api/v1", tags=["Notes"])  # satır 111
```

Router'ın kendi dahili prefix'i `/notes` olduğundan son URL: **`/api/v1/notes`** ✅

> Eğer bu importlar mevcut olmasaydı yapılması gereken eklemeler:
> ```python
> # main.py'daki import bloğuna ekle:
> from routers import notes
>
> # include_router bloğuna ekle:
> app.include_router(notes.router, prefix="/api/v1/notes", tags=["Notes"])
> ```

---

## 7. Yeni Python Bağımlılıkları

`requirements.txt` dosyasına aşağıdaki paketler eklenmiştir:

| Paket | Versiyon | Kullanım Amacı |
|---|---|---|
| `PyMuPDF` | `>=1.23.0` | PDF metin çıkarma (gömülü + OCR fallback) |
| `python-docx` | `>=1.1.0` | DOCX dosyalarından metin okuma |
| `pytesseract` | `>=0.3.10` | Tesseract OCR Python bağlayıcısı |
| `opencv-python` | `>=4.8.0` | Görsel ön işleme (CLAHE, Gaussian blur, Otsu) |
| `Pillow` | `>=10.0.0` | Görsel format dönüşümleri (PyMuPDF + pytesseract) |

### Kurulum

```bash
pip install -r requirements.txt
```

### ⚠️ Tesseract Sistem Kurulumu (Zorunlu)

`pytesseract` yalnızca Tesseract binary'sine Python wrapper'ıdır. **Sistem genelinde** Tesseract kurulumu ayrıca yapılmalıdır:

**Windows:**
```
https://github.com/UB-Mannheim/tesseract/wiki
```
Kurulum sonrası `pytesseract.pytesseract.tesseract_cmd` ayarlanmalıdır:
```python
# config.py veya settings başlangıcında:
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-tur
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

---

## 8. Postman / cURL Test Örnekleri

### Not Yükle (PDF)
```bash
curl -X POST http://localhost:8000/api/v1/notes \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -F "file=@/path/to/ders_notu.pdf"
```

### Not Yükle (Görsel OCR)
```bash
curl -X POST http://localhost:8000/api/v1/notes \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -F "file=@/path/to/not_gorseli.jpg"
```

### Notları Listele
```bash
curl -X GET http://localhost:8000/api/v1/notes \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

### Hatalı Format (400 beklenir)
```bash
curl -X POST http://localhost:8000/api/v1/notes \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -F "file=@/path/to/video.mp4"
```

---

## 9. Gelecek İyileştirme Önerileri

| Öneri | Öncelik | Açıklama |
|---|---|---|
| AES-256 şifreleme aktivasyonu | Yüksek | `raw_text_encrypted` alanları gerçekten şifrelenmeli |
| OCR kalite skoru | Orta | `ocr_quality_score` alanı Tesseract güven değeriyle doldurulabilir |
| Celery async işleme | Orta | Büyük dosyalar için arka plan görevi (mevcut `celery_tasks.py` ile entegrasyon) |
| DOCX tablo desteği genişletme | Düşük | Birleştirilmiş hücreler için özel parsing |
| OCR dil otomatik tespiti | Düşük | `langdetect` ile dil belirleme, lang parametresini dinamik set etme |

---

*Doküman otomatik oluşturulmuştur. ExamAI backend geliştirme ekibi – 2026-04-01*
