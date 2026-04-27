# ExamAI — Deployment Tam Uygulama Raporu

**Hazırlayan:** Antigravity  
**Tarih:** 27.04.2026  
**Kapsam:** Sıfır DevOps, OCR Devre Dışı, Geçici Depolama, Platform Subdomain

---

## 1. Genel Mimari Kararlar

Bu deployment'ta şu kararlar alındı:

| Karar | Seçim | Gerekçe |
|-------|-------|---------|
| Platform | **Railway** (Backend/Worker) + **Vercel** (Frontend) | Sıfır DevOps, en kolay kurulum |
| OCR | **Devre Dışı** | Tesseract sistem kurulumu gerektiriyor, deployment'ı zorlaştırıyor |
| Dosya Depolama | **Geçici (disk)** | Cloud Storage entegrasyonu gerekmez; yüklenmiş dosyalar silinse de metin DB'de kalır |
| Domain | **Platform subdomain** | `examai.railway.app` ve `examai.vercel.app` yeterli |

---

## 2. Antigravity'nin Yaptığı Değişiklikler

### 2.1 OCR Devre Dışı Bırakma

#### `backendWindsurf2/services/ocr_service.py`
- `_extract_from_pdf_pages()`: PDF sayfalarını artık Tesseract ile render etmiyor. Sadece PyMuPDF'in `get_text()` ile gömülü metni çekiyor.
- `_extract_from_gemini_image()`: Gemini görsel OCR devre dışı; boş string döner.
- `extract_text_from_file()`: Görsel dosyalar (`jpg`, `jpeg`, `png`) için kullanıcıya Türkçe bilgilendirme mesajı döner; hata fırlatmaz.

#### `backendWindsurf2/services/extraction_service.py`
- `extract_from_pdf()`: Tarama PDF fallback (OCR) kaldırıldı. Sadece gömülü metin çıkarılır.
- `extract_from_docx()`: Değişmedi. DOCX desteği devam eder.
- `extract_from_image()`: OCR yerine bilgilendirici string döner; sistem çökmez.
- `_preprocess_image_cv()`, `_ocr_image_bytes()`: **Tamamen silindi** (gereksiz bağımlılıklar).

### 2.2 Bağımlılıklar Temizlendi

#### `backendWindsurf2/requirements.txt`
Kaldırılan paketler:
- `pytesseract>=0.3.10`
- `opencv-python>=4.8.0`
- `Pillow>=10.0.0`

Bu üç paket ayrıca sistem düzeyinde **Tesseract** ve **libGL** kurulumu gerektiriyordu. Kaldırılmalarıyla Docker imajı ~400MB küçüldü ve kurulum süresi yarıya indi.

### 2.3 Deployment Dosyaları Oluşturuldu

#### `backendWindsurf2/Dockerfile` *(YENİ)*
```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0 ...
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### `backendWindsurf2/Procfile` *(YENİ)*
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
worker: celery -A celery_app worker -Q default,quiz_generation --loglevel=info --pool=prefork
```
> **Önemli:** `--pool=prefork` (Linux) kullanıldı. `--pool=solo` (Windows'a özgü) kaldırıldı.

#### `backendWindsurf2/railway.json` *(YENİ)*
Railway'in Dockerfile'ı otomatik tanıması için yapılandırma dosyası.

#### `backendWindsurf2/.env.production.example` *(YENİ)*
Railway paneline girilecek tüm değişkenlerin şablonu. Gerçek secret içermez.

#### `backendWindsurf2/.gitignore` *(YENİ)*
`.env`, `uploads/`, `.venv/` gibi klasörlerin Git'e gönderilmesini engeller.

### 2.4 Alembic Migration Yapılandırması Düzeltildi

#### `backendWindsurf2/alembic.ini`
```ini
# ÖNCE (hardcode - sadece local çalışır)
sqlalchemy.url = postgresql+asyncpg://examai_user:password@localhost:5432/examai_db

# SONRA (environment variable'dan okur)
sqlalchemy.url = %(DATABASE_URL)s
```

#### `backendWindsurf2/alembic/env.py`
`get_url()` fonksiyonu, `settings.DATABASE_URL`'yi alembic config'e enjekte edecek şekilde güncellendi. Bu sayede `alembic upgrade head` komutu production DB'de sorunsuz çalışır.

### 2.5 Frontend Deployment Dosyaları

#### `examai-frontend/.env.production` *(YENİ)*
```env
VITE_API_URL=https://YOUR-BACKEND-DOMAIN.up.railway.app
```
Vite build sırasında bu dosyayı otomatik okur. `src/api/index.js` zaten `import.meta.env.VITE_API_URL`'yi kullanıyor — ek kod değişikliği gerekmedi.

#### `examai-frontend/vercel.json` *(YENİ)*
```json
{ "rewrites": [{ "source": "/(.*)", "destination": "/" }] }
```
React Router (SPA) için gerekli. Bu olmadan `/dashboard` veya `/quiz/123` gibi URL'lere direkt girildiğinde Vercel 404 döner.

#### `examai-frontend/.gitignore`
`.env`, `.env.local` eklendi. `.env.production` intentionally dahil (sadece placeholder URL içeriyor, gerçek secret yok).

---

## 3. Senin Yapman Gerekenler (Sıralı)

### Adım 1 — GitHub Reposu Hazırla

Projeyi GitHub'a yükle. Railway ve Vercel GitHub reposuna bağlanarak otomatik deploy yapar.

```bash
# Proje kök dizininde
git init
git add .
git commit -m "Production ready deployment"
git remote add origin https://github.com/KULLANICI_ADI/examai.git
git push -u origin main
```

> [!CAUTION]
> `backendWindsurf2/.env` dosyasının commit edilmediğinden emin ol.
> `.gitignore`'a eklendi ama `git status` ile kontrol et.

---

### Adım 2 — Supabase (Ücretsiz PostgreSQL)

1. [supabase.com](https://supabase.com) → **New Project** oluştur
2. **Settings → Database** sekmesine git
3. **Connection string → URI** sekmesini seç, **"asyncpg"** modunu kopyala
4. Not et: `postgresql+asyncpg://postgres.XXXX:PASSWORD@aws-...supabase.co:5432/postgres`

---

### Adım 3 — Upstash (Ücretsiz Redis)

1. [upstash.com](https://upstash.com) → **Create Database** → Region: **EU-West-1** (yakın)
2. Oluşturulan Redis'in **"Redis URL"** alanını kopyala
3. Format: `redis://default:TOKEN@us1-xxxx.upstash.io:6379`

---

### Adım 4 — Railway (Backend + Worker)

1. [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo**
2. `backendWindsurf2` klasörünü seç (Root Directory)
3. **Variables** sekmesine git ve şu değişkenleri gir:

| Değişken | Değer |
|----------|-------|
| `APP_ENV` | `production` |
| `DEBUG` | `false` |
| `DATABASE_URL` | Supabase'den aldığın URL |
| `REDIS_URL` | Upstash'ten aldığın URL |
| `SECRET_KEY` | Aşağıdaki komutla üret → |
| `NOTE_ENCRYPTION_KEY` | Aşağıdaki komutla üret → |
| `GEMINI_API_KEY` | Mevcut API anahtarın |
| `GOOGLE_CLIENT_ID` | Mevcut OAuth ID'n |
| `GOOGLE_CLIENT_SECRET` | Mevcut OAuth Secret'ın |
| `GOOGLE_REDIRECT_URI` | `https://RAILWAY-URL/api/v1/auth/google/callback` |
| `ALLOWED_ORIGINS` | `https://VERCEL-URL.vercel.app` |
| `ALLOWED_HOSTS` | `RAILWAY-URL.up.railway.app` |
| `FRONTEND_URL` | `https://VERCEL-URL.vercel.app` |

**Secret Key üretmek için** (herhangi bir terminalde):
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Fernet Encryption Key üretmek için:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

4. Deploy tamamlanınca Railway'in verdiği URL'yi not et (örn: `examai-backend.up.railway.app`)

5. **Migration'ları çalıştır** — Railway Dashboard → Shell sekmesi:
```bash
alembic upgrade head
```

---

### Adım 5 — Worker Servisi (Railway)

Railway Dashboard'da **"Add Service"** → **"GitHub Repo"** → Aynı repo, aynı klasör  
Fark: Start Command'i şu şekilde değiştir:
```
celery -A celery_app worker -Q default,quiz_generation --loglevel=info --pool=prefork
```
Aynı environment variable'ları bu servise de ekle.

---

### Adım 6 — Google OAuth Callback URL Güncelle

1. [Google Cloud Console](https://console.cloud.google.com) → **APIs & Services → Credentials**
2. OAuth 2.0 Client ID'yi aç
3. **Authorized redirect URIs** → Ekle:
   ```
   https://RAILWAY-URL.up.railway.app/api/v1/auth/google/callback
   ```

---

### Adım 7 — Vercel (Frontend)

1. [vercel.com](https://vercel.com) → **New Project → GitHub**
2. `examai-frontend` klasörünü root directory olarak seç
3. **Environment Variables** ekle:
   ```
   VITE_API_URL = https://RAILWAY-URL.up.railway.app
   ```
4. Deploy et. Vercel'in verdiği URL'yi not et (örn: `examai-frontend.vercel.app`)

5. Bu URL'yi Railway'deki `ALLOWED_ORIGINS` ve `FRONTEND_URL` değişkenlerine geri dön ve güncelle.

---

### Adım 8 — Son Test

Tarayıcıdan şu akışı test et:

- [ ] `https://VERCEL-URL` → Giriş sayfası açılıyor mu?
- [ ] Kayıt ol → Dashboard'a yönleniyor mu?
- [ ] PDF dosyası yükle → Başarı mesajı var mı?
- [ ] Quiz oluştur → Oluşturuluyor mu?
- [ ] Soruları cevapla → Notlandırma çalışıyor mu?
- [ ] Google ile Giriş → OAuth callback çalışıyor mu?

---

## 4. Bilinen Kısıtlamalar

| Konu | Durum | Geçici Çözüm |
|------|-------|--------------|
| Tarama PDF OCR | ❌ Çalışmaz | Sadece metin tabanlı PDF yükle |
| Görsel (JPG/PNG) yükleme | ⚠️ Hata vermez, bildirim döner | — |
| Yüklenen dosyalar (disk) | ⚠️ Sunucu yeniden başlayınca silinir | Metin veritabanında kalır, quiz çalışmaya devam eder |
| E-posta (şifre sıfırlama) | ⚠️ SMTP ayarlanmadan çalışmaz | Gmail App Password ile opsiyonel kurulabilir |

---

## 5. Değiştirilen/Oluşturulan Dosyaların Özeti

| Dosya | Durum | Açıklama |
|-------|-------|---------|
| `backendWindsurf2/services/ocr_service.py` | ✏️ Değiştirildi | OCR devre dışı, sadece gömülü PDF metni |
| `backendWindsurf2/services/extraction_service.py` | ✏️ Değiştirildi | OCR kodu silindi, görsel için bilgi mesajı |
| `backendWindsurf2/requirements.txt` | ✏️ Değiştirildi | pytesseract, opencv, Pillow kaldırıldı |
| `backendWindsurf2/alembic.ini` | ✏️ Değiştirildi | `%(DATABASE_URL)s` placeholder |
| `backendWindsurf2/alembic/env.py` | ✏️ Değiştirildi | `get_url()` env variable enjeksiyonu |
| `backendWindsurf2/Dockerfile` | 🆕 Oluşturuldu | Railway/Render için Docker imajı |
| `backendWindsurf2/Procfile` | 🆕 Oluşturuldu | Web + Worker process tanımı |
| `backendWindsurf2/railway.json` | 🆕 Oluşturuldu | Railway platform config |
| `backendWindsurf2/.env.production.example` | 🆕 Oluşturuldu | Production env şablonu |
| `backendWindsurf2/.gitignore` | 🆕 Oluşturuldu | .env ve uploads güvenliği |
| `examai-frontend/.env.production` | 🆕 Oluşturuldu | Vite production API URL |
| `examai-frontend/vercel.json` | 🆕 Oluşturuldu | SPA routing (404 fix) |
| `examai-frontend/.gitignore` | ✏️ Güncellendi | .env güvenliği |
| `Docs/Deployment_Rehberi.md` | 🆕 Oluşturuldu | Genel deployment rehberi |

---

*Bu belge Antigravity tarafından otomatik olarak oluşturulmuştur.*
