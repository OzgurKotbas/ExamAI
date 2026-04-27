# ExamAI Backend — API Dokümantasyonu

**Versiyon:** 1.0.0 | **Framework:** FastAPI (Python 3.11+) | **Veritabanı:** PostgreSQL + SQLAlchemy Async

> Swagger UI: `http://localhost:8000/docs`  
> ReDoc:      `http://localhost:8000/redoc`

---

## İçindekiler

1. [Kurulum](#kurulum)
2. [Proje Yapısı](#proje-yapısı)
3. [Mimari Genel Bakış](#mimari-genel-bakış)
4. [Veritabanı Modelleri](#veritabanı-modelleri)
5. [API Endpoint Referansı](#api-endpoint-referansı)
   - [Auth](#auth-apiv1auth)
   - [Notes](#notes-apiv1notes)
   - [Quizzes](#quizzes-apiv1quizzes)
   - [Answers & Grading](#answers--grading-apiv1quizzesquiz_idsubmit)
   - [Analytics](#analytics-apiv1analytics)
6. [Kimlik Doğrulama](#kimlik-doğrulama)
7. [Servisler](#servisler)
8. [Token Optimizasyonu](#token-optimizasyonu)
9. [Hata Yönetimi](#hata-yönetimi)
10. [Güvenlik](#güvenlik)
11. [Deployment](#deployment)

---

## Kurulum

```bash
# 1. Depoyu klonla ve backend dizinine gir
cd backend

# 2. Sanal ortam oluştur
python -m venv .venv
.venv\Scripts\activate     # Windows
# source .venv/bin/activate  # Linux/macOS

# 3. Bağımlılıkları yükle
pip install -r requirements.txt

# 4. Ortam değişkenlerini ayarla
cp .env.example .env
# .env dosyasını gerçek API anahtarlarınızla doldurun

# 5. PostgreSQL ve Redis'i çalıştır (Docker örneği)
docker run -d --name pg -e POSTGRES_DB=examai_db -e POSTGRES_USER=examai_user \
  -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:16
docker run -d --name redis -p 6379:6379 redis:7

# 6. Uygulamayı başlat
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 7. Celery worker'ı (soru üretimi için ayrı terminal)
celery -A services.celery_tasks.celery_app worker --loglevel=info
```

---

## Proje Yapısı

```
backend/
├── main.py                    # FastAPI uygulama giriş noktası
├── config.py                  # Pydantic Settings (çevre değişkenleri)
├── database.py                # Async SQLAlchemy engine + session
├── requirements.txt
├── .env.example
│
├── models/                    # SQLAlchemy ORM modelleri
│   ├── user.py
│   ├── note.py
│   ├── quiz.py
│   ├── question.py
│   └── answer.py
│
├── schemas/                   # Pydantic request/response şemaları
│   ├── user.py
│   ├── note.py
│   ├── quiz.py
│   ├── question.py
│   └── answer.py
│
├── routers/                   # FastAPI Router'ları
│   ├── auth.py
│   ├── notes.py
│   ├── quiz.py
│   ├── answers.py
│   └── analytics.py
│
├── services/                  # İş mantığı katmanı
│   ├── auth_service.py        # JWT + Google OAuth
│   ├── image_service.py       # OpenCV ön işleme
│   ├── ocr_service.py         # Tesseract + Gemini OCR
│   ├── quiz_service.py        # Gemini soru üretimi
│   ├── grading_service.py     # Hibrit puanlama
│   ├── cache_service.py       # Redis önbellekleme
│   └── celery_tasks.py        # Async görev tanımları
│
└── utils/
    ├── security.py            # JWT + AES-256-GCM şifreleme
    ├── validators.py          # Gemini çıktı validasyonu
    └── logger.py              # structlog yapılandırması
```

---

## Mimari Genel Bakış

```
Kullanıcı (Browser/App)
        │
        ▼
  [FastAPI – main.py]
        │
   ┌────┴──────────────────────────────────────┐
   │                                           │
[Auth]  [Notes]  [Quiz]  [Answers]  [Analytics] ← Routers
   │       │       │         │
   ▼       ▼       ▼         ▼
[auth_service] [ocr_service] [quiz_service] [grading_service]
   │       │       │         │
   ▼       ▼       ▼         ▼
[PostgreSQL (async)] + [Redis (cache + Celery broker)]
                         │
                    [Celery Worker]
                         │
                   [Gemini 1.5 Flash]
```

---

## Veritabanı Modelleri

### User
| Sütun | Tip | Açıklama |
|---|---|---|
| id | UUID PK | |
| email | VARCHAR(255) UNIQUE | |
| full_name | VARCHAR(255) | |
| hashed_password | VARCHAR(255) | OAuth kullanıcıları için NULL |
| picture_url | VARCHAR(512) | |
| is_active | BOOLEAN | |
| is_google_auth | BOOLEAN | |
| created_at / updated_at | TIMESTAMP TZ | |

### Note
| Sütun | Tip | Açıklama |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK → users | |
| context_id | VARCHAR(128) UNIQUE | Not için sabit referans ID |
| original_filename | VARCHAR(255) | |
| file_type | VARCHAR(20) | `image` \| `pdf` \| `text` |
| raw_text_encrypted | TEXT | AES-256-GCM şifreli |
| cleaned_text_encrypted | TEXT | AES-256-GCM şifreli |
| ocr_quality_score | FLOAT | 0-1 arası keskinlik skoru |
| created_at | TIMESTAMP TZ | |

### Quiz
| Sütun | Tip | Açıklama |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK → users | |
| note_id | UUID FK → notes | |
| total_questions | INT | |
| mc_ratio | NUMERIC(3,2) | Çoktan seçmeli oranı (0-1) |
| difficulty | VARCHAR(20) | `easy` \| `medium` \| `hard` |
| parameters | JSONB | Ham parametre anlık görüntüsü |
| status | VARCHAR(20) | `pending` \| `generating` \| `ready` \| `failed` |
| cache_key | VARCHAR(256) | Redis önbellek referansı |
| created_at / completed_at | TIMESTAMP TZ | |

### Question
| Sütun | Tip | Açıklama |
|---|---|---|
| id | UUID PK | |
| quiz_id | UUID FK → quizzes | |
| type | VARCHAR(20) | `multiple_choice` \| `open_ended` |
| text | TEXT | |
| options | JSONB | `{A:.., B:.., C:.., D:..}` (MC için) |
| correct_answer | VARCHAR(4) | `A/B/C/D` (MC için) |
| topic | VARCHAR(128) | Gemini tarafından otomatik etiketlenir |
| difficulty | VARCHAR(20) | |
| rubric | TEXT | Açık uçlu değerlendirme kılavuzu |
| order_index | INT | |

### Answer
| Sütun | Tip | Açıklama |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK → users | |
| question_id | UUID FK → questions | |
| user_answer | TEXT | |
| score | INT | 0-100 |
| feedback | TEXT | |
| is_ai_graded | BOOLEAN | MC için False, açık uçlu için True |
| graded_at / submitted_at | TIMESTAMP TZ | |

---

## API Endpoint Referansı

Tüm endpoint'ler `/api/v1` önekiyle başlar.  
Korumalı endpoint'ler `Authorization: Bearer <JWT>` başlığı gerektirir.

---

### Auth `/api/v1/auth`

#### `POST /register` — Kayıt
Yeni kullanıcı oluşturur ve JWT döndürür.

**Request Body (JSON):**
```json
{
  "email": "ali@example.com",
  "full_name": "Ali Yılmaz",
  "password": "GüçlüŞifre123!"
}
```

**Response 201:**
```json
{
  "access_token": "<JWT>",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "ali@example.com",
    "full_name": "Ali Yılmaz",
    "is_active": true,
    "is_google_auth": false,
    "created_at": "2026-03-25T12:00:00Z"
  }
}
```

---

#### `POST /login` — Giriş (Form)
E-posta ve şifreyle giriş.

**Request Body (form-data):**
```
email=ali@example.com
password=GüçlüŞifre123!
```

**Response 200:** TokenResponse (yukarıdakiyle aynı)

---

#### `GET /google` — Google OAuth Başlat
Kullanıcıyı Google onay ekranına yönlendirir.

**Response 302 Redirect** → Google OAuth URL

---

#### `GET /google/callback` — Google OAuth Callback
Google'ın code parametresini alır ve JWT döndürür.

**Query Params:** `code=<auth_code>`  
**Response 200:** TokenResponse

---

### Notes `/api/v1/notes`

> 🔒 Tüm endpoint'ler JWT gerektirir.

#### `POST /upload` — Not Yükle
Resim, PDF veya metin dosyası yükler; OCR işlemi tetiklenir.

**Request:** `multipart/form-data`
| Alan | Tip | Açıklama |
|---|---|---|
| file | File | JPG, PNG, PDF, TXT |
| strategy | string | `tesseract_gemini` (default) veya `gemini_direct` |

**Response 201:**
```json
{
  "note": {
    "id": "uuid",
    "context_id": "uuid",
    "original_filename": "ders_notu.pdf",
    "file_type": "pdf",
    "ocr_quality_score": 0.85,
    "created_at": "2026-03-25T12:00:00Z"
  },
  "message": "Note uploaded and processed successfully."
}
```

**Hata Durumları:**
- `415` — Desteklenmeyen dosya türü
- `413` — Dosya boyutu aşıldı (varsayılan 20MB)
- `422` — Görüntü kalitesi çok düşük

---

#### `GET /` — Notları Listele
Kullanıcıya ait tüm notları döndürür (içerik dahil değil).

**Response 200:** `NoteRead[]`

---

#### `GET /{note_id}` — Not Detayı
Şifresi çözülmüş `cleaned_text` dahil detay döndürür.

**Response 200:**
```json
{
  "id": "uuid",
  "context_id": "uuid",
  "original_filename": "...",
  "file_type": "image",
  "ocr_quality_score": 0.9,
  "created_at": "...",
  "cleaned_text": "Çıkarılan ve temizlenmiş metin..."
}
```

---

#### `DELETE /{note_id}` — Not Sil
**Response 204 No Content**

---

### Quizzes `/api/v1/quizzes`

> 🔒 Tüm endpoint'ler JWT gerektirir.

#### `POST /` — Sınav Oluştur
Yeni bir sınav başlatır. Aynı parametrelerle daha önce oluşturulmuşsa önbellekten döndürür.

**Request Body (JSON):**
```json
{
  "note_id": "uuid",
  "total_questions": 10,
  "mc_ratio": 0.7,
  "difficulty": "medium"
}
```

**Response 202:**
```json
{
  "quiz_id": "uuid",
  "status": "pending",
  "message": "Quiz is being generated. Poll /quizzes/{quiz_id}/status for updates."
}
```

**Not:** `mc_ratio=0.7` → 7 çoktan seçmeli + 3 açık uçlu soru.

---

#### `GET /{quiz_id}/status` — Durum Sorgula
Sınav oluşturma durumunu döndürür.

**Response 200:**
```json
{
  "quiz_id": "uuid",
  "status": "ready",
  "message": "Quiz is ready!"
}
```

| Status | Anlamı |
|---|---|
| `pending` | Sıraya alındı |
| `generating` | Gemini ile üretiliyor |
| `ready` | Hazır, sorular çekilebilir |
| `failed` | Üretim başarısız oldu |

---

#### `GET /{quiz_id}/questions` — Soruları Getir
Sınav hazır olduğunda soruları döndürür. **Doğru cevap dahil değildir.**

**Response 200:** `QuestionRead[]`
```json
[
  {
    "id": "uuid",
    "quiz_id": "uuid",
    "type": "multiple_choice",
    "text": "Türev nedir?",
    "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
    "topic": "Türev",
    "difficulty": "medium",
    "rubric": null,
    "order_index": 0
  }
]
```

---

#### `GET /` — Sınavları Listele
**Response 200:** `QuizRead[]`

---

### Answers & Grading `/api/v1/quizzes/{quiz_id}/submit`

#### `POST /{quiz_id}/submit` — Sınav Gönder & Puanla
Tüm cevapları gönderir; anında hibrit puanlama yapılır.

**Request Body (JSON):**
```json
{
  "answers": [
    {"question_id": "uuid", "user_answer": "A"},
    {"question_id": "uuid", "user_answer": "Türev, bir fonksiyonun anlık değişim hızıdır."}
  ]
}
```

**Response 200 — AnalyticsResponse:**
```json
{
  "total_score": 72.5,
  "total_questions": 10,
  "correct_mc": 5,
  "topic_breakdown": {
    "Türev": {"total": 4, "correct": 3, "avg_score": 80.0},
    "İntegral": {"total": 3, "correct": 1, "avg_score": 45.0}
  },
  "weak_topics": ["İntegral"],
  "answers": [
    {
      "id": "uuid",
      "question_id": "uuid",
      "user_answer": "A",
      "score": 100,
      "feedback": "✓ Doğru! Cevap: A",
      "is_ai_graded": false,
      "graded_at": "2026-03-25T12:05:00Z"
    }
  ]
}
```

**Puanlama Mantığı:**
- **Çoktan seçmeli:** Backend anında karşılaştırır (AI kullanılmaz) → 0 veya 100
- **Açık uçlu:** Gemini 1.5 Flash semantik değerlendirme yapar → 0-100 + gerekçe

---

### Analytics `/api/v1/analytics`

> 🔒 JWT gerektirir.

#### `GET /summary` — Genel Performans Özeti
Tüm zamanların analitik özetini döndürür.

**Response 200:**
```json
{
  "total_quizzes": 12,
  "total_answers": 120,
  "avg_score": 68.3,
  "topics": {
    "Türev": {"total": 30, "avg_score": 80.0},
    "İntegral": {"total": 25, "avg_score": 52.4}
  },
  "weak_topics": ["İntegral", "Limit"],
  "recommendations": [
    "İntegral konusuna tekrar çalışmanız önerilir.",
    "Limit konusuna tekrar çalışmanız önerilir."
  ]
}
```

---

## Kimlik Doğrulama

Backend JWT Bearer Token tabanlı kimlik doğrulama kullanır.

```
Authorization: Bearer <access_token>
```

- **Token süresi:** 60 dakika (`.env`'den yapılandırılabilir)
- Google OAuth kullanıcıları `GET /auth/google` ile giriş yapar
- Tüm token'lar HTTP-only cookie ile sağlanabilir (XSS koruması için önerilir)

---

## Servisler

### auth_service.py
- `register_user()` — Bcrypt hash ile kayıt
- `authenticate_user()` — E-posta/şifre doğrulama + JWT üretimi
- `google_login_or_create()` — OAuth code exchange + upsert kullanıcı
- `get_current_user()` — FastAPI bağımlılık enjeksiyonu

### image_service.py
OpenCV pipeline:
1. Max 1024×1024 boyutlandırma
2. Gri tonlama
3. fastNlMeansDenoising (gürültü azaltma)
4. CLAHE kontrast artırma
5. Laplacian tabanlı deskew (açı düzeltme)

`estimate_quality()` — Laplacian varyansı ile 0-1 arası keskinlik skoru.

### ocr_service.py
| Strateji | Akış |
|---|---|
| `tesseract_gemini` | Tesseract OCR → Gemini metin temizleme |
| `gemini_direct` | Doğrudan Gemini multimodal çıkarma |

PDF sayfaları PyMuPDF ile 200 DPI JPEG olarak render edilir.

### quiz_service.py
1. **Zayıf konu tespiti:** Answer tablosundan avg < 60 olan konular sorgulanır
2. **Token optimizasyonu:** 12.000 karakterden uzun notlar özetlenir
3. **Toplu prompt:** Hem MC hem açık uçlu tek istek
4. **Validasyon:** Pydantic şemasıyla JSON doğrulanır
5. **Yeniden deneme:** 3 deneme, üstel geri çekilme

### grading_service.py
- **MC:** `user_answer.upper() == correct_answer.upper()` → 0/100
- **Açık uçlu:** Gemini prompt → `{puan, geri_bildirim}` JSON → Pydantic validasyonu

### cache_service.py
```
Cache key = SHA-256(user_id:note_id:total_questions:mc_ratio:difficulty)
TTL = 24 saat
```

---

## Token Optimizasyonu

| Strateji | Uygulama |
|---|---|
| MC puanlamada AI kullanılmaz | `grading_service.py` |
| Uzun notlar özetlenir | `quiz_service._summarise_if_needed()` |
| Önbellekleme | Redis + SHA-256 anahtar |
| Toplu üretim | Tek prompt → MC + Açık uçlu |

---

## Hata Yönetimi

| Durum | Davranış |
|---|---|
| Gemini geçersiz JSON | 3 deneme + üstel bekleme |
| Quiz üretim hatası | `quiz.status = "failed"` + kullanıcı bildirimi |
| API rate limit | Exponential backoff (`time.sleep(2**attempt)`) |
| Düşük OCR kalitesi | 422 ile kullanıcıya açıklama |
| JWT süresi dolmuş | 401 Unauthorized |

Tüm hatalar `structlog` ile JSON formatında loglanır.

---

## Güvenlik

| Özellik | Uygulama |
|---|---|
| Kullanıcı notları şifreleme | AES-256-GCM (`utils/security.py`) |
| Şifre hashing | Bcrypt (passlib) |
| Token | JWT (HS256, `python-jose`) |
| CORS | `FastAPI CORSMiddleware` |
| Veri anonimleştirme | Gemini'ye kullanıcı adı gönderilmez |
| HTTPS | Production'da zorunlu |

---

## Deployment

### Backend (Railway / Google Cloud Run)
```dockerfile
# Dockerfile (örnek)
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Ortam Değişkenleri
Production'da tüm `.env` değerlerini platform gizli değişkenleri (**Secrets**) olarak tanımlayın:
- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `GEMINI_API_KEY`
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`
- `NOTE_ENCRYPTION_KEY`

### Celery Worker
```bash
celery -A services.celery_tasks.celery_app worker \
  --loglevel=info --concurrency=4
```

---

*Bu döküman ExamAI v1.0.0 backend'ine aittir. Güncel endpoint listesi için `http://localhost:8000/docs` adresini ziyaret edin.*
