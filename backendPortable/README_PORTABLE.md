# ExamAI Backend (Portable) - Docker/Compose

Bu klasör, `backendWindsurf2` kodunun her PC'de aynı şekilde çalışması için Docker/Compose ile taşınabilir hale getirilmiş sürümüdür.

## Gereksinimler
- Docker Desktop (Windows) veya Docker Engine
- Docker Compose (Docker Desktop ile genelde hazır gelir)

## 1) Env dosyası
`backendPortable/.env` dosyasını oluşturun:

- `.env.example` yerine: bu klasördeki `.env.docker.example` dosyasını kopyalayın.
- Kendi değerlerinizi girin (özellikle `DATABASE_URL`, `NOTE_ENCRYPTION_KEY`, `GEMINI_API_KEY`).

Öneri:
1. `.env.docker.example` -> `.env`
2. `NOTE_ENCRYPTION_KEY` için 32-byte base64 anahtar üretip yapıştırın.

## 2) Başlatma
`backendPortable` klasöründen:

```bash
docker compose up --build
```

- `api`: FastAPI server (`http://localhost:8000`)
- `worker`: Celery worker (quiz/note arka plan görevleri)
- `redis`: cache/broker
- `postgres`: uygulama veritabanı

## 3) API test örnekleri

Health:
`GET http://localhost:8000/health`

Swagger:
`http://localhost:8000/docs`

Auth:
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me?token=ACCESS_TOKEN`

Quizzes:
- `POST /api/v1/quizzes`
- `GET /api/v1/quizzes/{quiz_id}/status`
- `GET /api/v1/quizzes/{quiz_id}/questions`

Not: `POST /api/v1/quizzes`, `notes` tablosunda ilgili `note_id` için `cleaned_text_encrypted` dolu olmasını bekler.

## 4) Notlar
- OCR / note processing Celery task'leri (varsa) için Tesseract binary container içinde kurulu (ama dil dosyaları sistemden sisteme değişebilir).
- Google OAuth ve Gemini quiz üretimi opsiyoneldir; ama çalışması için gerekli env değerleri doldurulmalıdır.

