# Portable Backend Kurulumu (Docker/Compose)

**Tarih:** 2026-03-30  
**Saat:** 11:23:12  

## Amaç
`backendWindsurf2` kodunu, farklı PC'lerde aynı şekilde çalıştırılabilmesi için `backendPortable` altında Docker/Compose ile paketleyip dağıtılabilir hale getirmek.

## Oluşturulan klasörler
- `backendPortable/` (kopyalanmış backend kodu + Docker dosyaları)
- `Docs/backendReport/` (bu kayıt)

## Dosyalar
`backendPortable` içinde:
- `Dockerfile`
- `docker-compose.yml`
- `.env.docker.example`
- `README_PORTABLE.md`

## Kurulum adımları (her PC’de)
1. `backendPortable` klasörünü o PC’ye kopyalayın.
2. `backendPortable/.env` dosyasını oluşturun (şablon: `.env.docker.example`).
3. `backendPortable` klasöründe:
   - `docker compose up --build`
4. API erişimi:
   - `http://localhost:8000/health`
   - `http://localhost:8000/docs`

## Kritik konfigürasyonlar
- `DATABASE_URL`: PostgreSQL bağlantısı (compose servisine göre `postgres` host adı kullanılmalı).
- `REDIS_URL`: Redis bağlantısı (compose servisine göre `redis` host adı kullanılmalı).
- `NOTE_ENCRYPTION_KEY`: Not şifreleme/çözme için 32-byte base64 anahtar.
- `GEMINI_API_KEY`: Quiz üretimi için (opsiyonel; env boşsa quiz üretim adımı patlayabilir).

## Alınan notlar
- Bu kurulum “her PC’de çalışsın” hedefini Docker ile standardize eder.
- Not OCR / note processing Celery task’leri çalıştırılırsa Tesseract / dil paketleri container içinde gerekli olabilir.

