# ExamAI – backendWindsurf2 Kurulum & Postman Test Rehberi

> **Güncel Durum (2026-04-05):** Alembic migration sıfırlandı ve yeniden oluşturuldu (`e10d3714e2a9`).  
> Not yükleme endpoint'i (`POST /api/v1/notes`) aktif ve şifreleme düzeltmesi uygulandı.

---

## Genel Bakış

| Bileşen | Teknoloji | Port |
|---------|-----------|------|
| FastAPI | uvicorn | **8001** |
| PostgreSQL | Docker | 5432 |
| Redis | Docker | 6379 |
| Celery Worker | solo pool | — |
| Swagger UI | — | `http://localhost:8001/docs` |

**Base URL:** `http://localhost:8001/api/v1`

---

## BÖLÜM 1 — Ön Koşullar

### 1.1 Python Sürümü
```powershell
python --version   # 3.11+ önerilir
```

### 1.2 Docker (PostgreSQL + Redis)

```powershell
# PostgreSQL başlat
docker run -d --name pg `
  -e POSTGRES_DB=examai_db `
  -e POSTGRES_USER=examai_user `
  -e POSTGRES_PASSWORD=password `
  -p 5432:5432 `
  postgres:16

# Redis başlat
docker run -d --name redis `
  -p 6379:6379 `
  redis:7

# Doğrula
docker ps
```

> **İkinci çalıştırmada** container zaten duruyorsa:  
> ```powershell
> docker start pg redis
> ```

---

## BÖLÜM 2 — Kurulum

### 2.1 Virtual Environment

```powershell
cd "C:\Users\ozgur\Desktop\EXAM_AI\backendWindsurf2"
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 2.2 Bağımlılıkları Yükle

```powershell
pip install -r requirements.txt
```

### 2.3 .env Dosyasını Hazırla

```powershell
Copy-Item .env.example .env -Force
```

Ardından `.env` dosyasını açıp şu alanları düzenleyin:

| Alan | Ne Yapmalı |
|------|------------|
| `SECRET_KEY` | Güvenli bir değer üret (aşağıdaki komut) |
| `NOTE_ENCRYPTION_KEY` | Güvenli bir değer üret (aşağıdaki komut) |
| `GEMINI_API_KEY` | Gerçek Gemini API anahtarını yaz |
| `DATABASE_URL` | Docker kurulumuna göre zaten doğru |
| `REDIS_URL` | `redis://localhost:6379/0` — dokunma |

**SECRET_KEY üretme:**
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

**NOTE_ENCRYPTION_KEY üretme (Base64, 32 byte):**
```powershell
python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

---

## BÖLÜM 3 — Veritabanı Migration

> ⚠️ Migration daha önce `aaa774a83dda` hatası veriyordu. Bu sorun çözüldü.  
> `alembic/versions/` klasöründe artık `e10d3714e2a9_initial_migration.py` mevcut.

### 3.1 Migration Durumunu Kontrol Et

```powershell
alembic current
# Beklenen çıktı: e10d3714e2a9 (head)
```

### 3.2 Migration Henüz Uygulanmadıysa

```powershell
alembic upgrade head
```

### 3.3 Alembic Hayalet Revizyon Hatası Aldıysanız

```powershell
# 1. Veritabanındaki eski revizyon kaydını sil
python -c "
import asyncio, asyncpg
async def reset():
    conn = await asyncpg.connect('postgresql://examai_user:password@localhost:5432/examai_db')
    await conn.execute('DELETE FROM alembic_version')
    await conn.close()
    print('Temizlendi!')
asyncio.run(reset())
"

# 2. Yeni migration oluştur
alembic revision --autogenerate -m \"Initial migration\"

# 3. Uygula
alembic upgrade head
```

---

## BÖLÜM 4 — Uygulamayı Başlatma

> **3 ayrı terminal** gereklidir: FastAPI, Celery, (isteğe bağlı) Redis monitor.

### Terminal 1 — FastAPI

```powershell
cd "C:\Users\ozgur\Desktop\EXAM_AI\backendWindsurf2"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8001cd
```

✅ Başarılı çıktı: `Application startup complete.`

### Terminal 2 — Celery Worker

```powershell
cd "C:\Users\ozgur\Desktop\EXAM_AI\backendWindsurf2"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
celery -A celery_app worker --loglevel=info --pool=solo
```

> `--pool=solo` Windows'ta zorunludur (multiprocessing fork sorunu).

### Tesseract OCR (Görsel yükleme için)

Sadece `.jpg`, `.jpeg`, `.png` yükleyecekseniz gereklidir:
1. https://github.com/UB-Mannheim/tesseract/wiki adresinden indirin
2. Kurulumda **Türkçe dil paketini** seçin
3. Doğrulama: `tesseract --version`

---

## BÖLÜM 5 — Sağlık Kontrolü

```
GET http://localhost:8001/health
GET http://localhost:8001/docs       ← Swagger UI
```

---

## BÖLÜM 6 — Postman ile Adım Adım Test

> **Önemli:** Her yetkili endpoint için `Authorization: Bearer <token>` header'ı zorunludur.

---

### ADIM 1 — Kullanıcı Kaydı (Register)

```
POST http://localhost:8001/api/v1/auth/register
```

**Headers:**
```
Content-Type: application/json
```

**Body (raw → JSON):**
```json
{
  "email": "test@example.com",
  "full_name": "Test Kullanıcı",
  "password": "GuvenliSifre123!"
}
```

**Başarılı Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5...",
  "token_type": "bearer",
  "user": {
    "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "email": "test@example.com",
    "full_name": "Test Kullanıcı",
    "is_active": true
  }
}
```

➡️ `access_token` değerini kopyalayın.

---

### ADIM 2 — Giriş (Login)

```
POST http://localhost:8001/api/v1/auth/login
```

**Headers:**
```
Content-Type: application/x-www-form-urlencoded
```

**Body (x-www-form-urlencoded):**
```
email     = test@example.com
password  = GuvenliSifre123!
```

> ⚠️ Login endpoint'i JSON **değil**, form-encoded kabul eder.

**Başarılı Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5...",
  "token_type": "bearer"
}
```

---

### ADIM 3 — Profil Görüntüle (Auth Testi)

```
GET http://localhost:8001/api/v1/auth/me
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Başarılı Response (200):**
```json
{
  "id": "xxxxxxxx-...",
  "email": "test@example.com",
  "full_name": "Test Kullanıcı",
  "is_active": true,
  "is_google_auth": false
}
```

---

### ADIM 4 — Not Yükle (Upload Note)

> ✅ Bu adım Alembic fix sonrası çalışır. Metin AES-256-GCM ile şifrelenerek kaydedilir.

```
POST http://localhost:8001/api/v1/notes
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body (form-data):**  
Key: `file` → **File** tipinde → İstediğiniz dosyayı seçin

| Desteklenen Format | Maksimu Boyut |
|-------------------|---------------|
| `.txt` | 20 MB |
| `.pdf` | 20 MB |
| `.docx` | 20 MB |
| `.jpg` / `.jpeg` / `.png` | 20 MB (Tesseract gerekli) |

**Başarılı Response (201):**
```json
{
  "message": "Note uploaded successfully",
  "note_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

➡️ `note_id` değerini kopyalayın — quiz oluşturmak için gerekli.

---

### ADIM 5 — Notları Listele

```
GET http://localhost:8001/api/v1/notes
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Başarılı Response (200):**
```json
{
  "notes": [
    {
      "note_id": "xxxxxxxx-...",
      "context_id": "xxxxxxxx-...",
      "original_filename": "ders_notu.pdf",
      "file_type": "pdf",
      "created_at": "2026-04-05T12:00:00"
    }
  ],
  "total": 1
}
```

---

### ADIM 6 — Quiz Oluştur

```
POST http://localhost:8001/api/v1/quizzes
```

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body (raw → JSON):**
```json
{
  "note_id": "<ADIM-4'ten_aldığınız_note_id>",
  "total_questions": 10,
  "mc_ratio": 0.7,
  "difficulty": "medium"
}
```

| Alan | Açıklama | Değer Aralığı |
|------|----------|---------------|
| `total_questions` | Toplam soru sayısı | 1–50 |
| `mc_ratio` | Çoktan seçmeli oran | 0.0–1.0 |
| `difficulty` | Zorluk | `easy` / `medium` / `hard` |

**Başarılı Response (202 Accepted):**
```json
{
  "quiz_id": "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy",
  "status": "pending",
  "message": "Quiz is being generated. Poll /quizzes/{quiz_id}/status for updates."
}
```

➡️ `quiz_id` değerini kopyalayın.

> ⚠️ `GEMINI_API_KEY` boşsa Celery task başarısız olur, quiz `failed` durumuna geçer.

---

### ADIM 7 — Quiz Durumunu Sorgula (Status Polling)

```
GET http://localhost:8001/api/v1/quizzes/<quiz_id>/status
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Olası Response Durumları:**
```json
{ "quiz_id": "...", "status": "pending",    "message": "Quiz is queued for generation." }
{ "quiz_id": "...", "status": "generating", "message": "Quiz is currently being generated..." }
{ "quiz_id": "...", "status": "ready",      "message": "Quiz is ready!" }
{ "quiz_id": "...", "status": "failed",     "message": "Quiz generation failed. Please try again." }
```

> Celery işlemi genellikle 10–30 saniye sürer. `status: ready` görene kadar polling yapın.

---

### ADIM 8 — Quiz Listesi

```
GET http://localhost:8001/api/v1/quizzes
```

**Headers:**
```
Authorization: Bearer <access_token>
```

---

### ADIM 9 — Soruları Al

> `status: ready` olduktan sonra çalışır.

```
GET http://localhost:8001/api/v1/quizzes/<quiz_id>/questions
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Başarılı Response (200):**
```json
[
  {
    "id": "qqqqqqqq-...",
    "quiz_id": "yyyyyyyy-...",
    "type": "multiple_choice",
    "text": "Soru metni burada?",
    "options": { "A": "Seçenek A", "B": "Seçenek B", "C": "Seçenek C", "D": "Seçenek D" },
    "topic": "Konu adı",
    "difficulty": "medium",
    "rubric": null,
    "order_index": 0
  }
]
```

> 🔒 `correct_answer` bu aşamada döndürülmez — sadece submit sonrası görülür.

---

### ADIM 10 — Quiz Cevaplarını Gönder (Submit)

```
POST http://localhost:8001/api/v1/quizzes/<quiz_id>/submit
```

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body (raw → JSON):**
```json
{
  "quiz_id": "<quiz_id>",
  "answers": [
    {
      "question_id": "<question_id_1>",
      "user_answer": "A"
    },
    {
      "question_id": "<question_id_2>",
      "user_answer": "Açık uçlu cevap metni buraya..."
    }
  ]
}
```

**Başarılı Response (202):**
```json
{
  "grading_id": "zzzzzzzz-...",
  "quiz_id": "yyyyyyyy-...",
  "status": "pending",
  "message": "Quiz is being graded. Poll /quizzes/{quiz_id}/grading/{grading_id} for updates."
}
```

---

### ADIM 11 — Grading Durumunu Sorgula

```
GET http://localhost:8001/api/v1/quizzes/<quiz_id>/grading/<grading_id>/status
```

**Headers:**
```
Authorization: Bearer <access_token>
```

---

### ADIM 12 — Grading Sonuçlarını Al

```
GET http://localhost:8001/api/v1/quizzes/<quiz_id>/grading/<grading_id>
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Başarılı Response (200):**
```json
{
  "quiz_id": "yyyyyyyy-...",
  "total_score": 750,
  "max_score": 1000,
  "percentage": 75.0,
  "grading_results": [
    {
      "question_id": "qqqqqqqq-...",
      "score": 100,
      "feedback": "Doğru cevap!",
      "key_points_covered": [],
      "missing_points": [],
      "suggestions": []
    }
  ],
  "completed_at": "2026-04-05T12:30:00"
}
```

---

## BÖLÜM 7 — Akış Özeti (Hızlı Referans)

```
[1] POST /auth/register     → access_token al
[2] POST /auth/login        → access_token al  (zaten kayıtlıysan)
[3] GET  /auth/me           → token geçerli mi kontrol et

[4] POST /notes             → Dosya yükle → note_id al  ✅ ŞİFRELEME AKTİF
[5] GET  /notes             → Notlarını listele

[6] POST /quizzes           → Quiz oluştur (note_id gerekli) → quiz_id al
[7] GET  /quizzes/{id}/status → "ready" olana kadar sorgula
[8] GET  /quizzes           → Tüm quizlerin listesi

[9] GET  /quizzes/{id}/questions  → Soruları al (ready olmalı)

[10] POST /quizzes/{id}/submit    → Cevapları gönder → grading_id al
[11] GET  /quizzes/{id}/grading/{gid}/status → "completed" olana kadar sorgula
[12] GET  /quizzes/{id}/grading/{gid}        → Sonuçları al
```

---

## BÖLÜM 8 — Sık Karşılaşılan Hatalar

| Hata Kodu | Mesaj | Çözüm |
|-----------|-------|-------|
| `401 Unauthorized` | Missing / Invalid Authorization header | Token değerini kontrol et, süresi dolmuş olabilir |
| `400 Bad Request` | `NOTE_ENCRYPTION_KEY is not set` | `.env`'de `NOTE_ENCRYPTION_KEY` placeholder değiştir |
| `400 Bad Request` | `Dosya boş` | Dosya içeriği var mı kontrol et |
| `400 Bad Request` | `Desteklenmeyen format` | pdf, docx, txt, jpg, jpeg, png kullan |
| `400 Bad Request` | `Note content is too short` | En az 50 karakter içeren not yükle |
| `404 Not Found` | Note bulunamadı | `note_id` doğru mu? Başka user'a mı ait? |
| `409 Conflict` | Quiz not ready yet | Status polling yap, `ready` bekle |
| `500` | Failed to decrypt text | Notun `NOTE_ENCRYPTION_KEY` ile şifrelendiğinden emin ol |
| Quiz `failed` | — | Celery worker çalışıyor mu? `GEMINI_API_KEY` dolu mu? |
| DB bağlantı hatası | — | `docker ps` — pg ve redis çalışıyor mu? |
| Alembic revision hatası | `Can't locate revision` | Bölüm 3.3 adımlarını izle |

---

## BÖLÜM 9 — Faydalı Debug Komutları

```powershell
# Container durumu
docker ps

# Alembic migration durumu
alembic current
alembic history

# DB içindeki tabloları gör (asyncpg ile)
python -c "
import asyncio, asyncpg
async def show():
    conn = await asyncpg.connect('postgresql://examai_user:password@localhost:5432/examai_db')
    rows = await conn.fetch(\"SELECT tablename FROM pg_tables WHERE schemaname='public'\")
    [print(r['tablename']) for r in rows]
    await conn.close()
asyncio.run(show())
"

# Redis'e bağlan
docker exec -it redis redis-cli ping   # PONG dönmeli

# Celery task geçmişi (Redis'ten)
docker exec -it redis redis-cli keys "celery*"
```

---

*Son güncelleme: 2026-04-05 — Alembic fix, şifreleme düzeltmesi ve notes endpoint eklenmesi sonrası yeniden düzenlendi.*
