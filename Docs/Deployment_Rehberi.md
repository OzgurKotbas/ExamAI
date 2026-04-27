# ExamAI Deployment (Canlıya Alma) Rehberi

Bu belge, ExamAI projesinin yerel ortamdan (localhost) internete (production) taşınması için gereken teknik adımları ve stratejileri içerir.

## 1. Mimari Genel Bakış
Projenin tam fonksiyonel çalışabilmesi için 5 ana bileşenin bulutta host edilmesi gerekir:
- **Frontend:** React + Vite (Statik dosyalar)
- **Backend:** FastAPI (Ana API)
- **Worker:** Celery (Arka plan görevleri - Quiz oluşturma)
- **Veritabanı:** PostgreSQL
- **Mesaj Kuyruğu:** Redis

---

## 2. Gerekli Teknik Değişiklikler

### Backend & Worker (.env)
Aşağıdaki değişkenlerin production değerleriyle güncellenmesi zorunludur:
- `DEBUG=false`
- `APP_ENV=production`
- `DATABASE_URL`: Managed DB bağlantı adresi (Supabase/Neon/Railway).
- `REDIS_URL`: Managed Redis adresi (Upstash/Railway).
- `ALLOWED_ORIGINS`: Frontend'in canlı adresi (örn: `https://exam-ai.vercel.app`).
- `SECRET_KEY`: Yeni, güvenli bir hash (Python `secrets` modülü ile üretilmeli).

### Frontend (.env)
- `VITE_API_URL`: Backend'in canlı API adresi.

### OCR (Kritik!)
Proje **Tesseract OCR** kullandığı için, seçilecek sunucuda (veya Docker imajında) aşağıdaki paketlerin yüklü olması gerekir:
- `tesseract-ocr`
- `tesseract-ocr-tur` (Türkçe desteği için)
- `libgl1` (OpenCV bağımlılığı için)

---

## 3. Platform Karşılaştırması

### Seçenek A: Railway (Önerilen - Kolay)
- **Maliyet:** Aylık minimum 5$ (Hobby Plan).
- **Avantajlar:** Tek tıkla PostgreSQL, Redis ve Docker desteği. Kurulumu en hızlı yöntemdir.
- **Trial:** Yeni üyelere tek seferlik 5$ kredi verilir (yaklaşık 1 ay yeterlidir).

### Seçenek B: Tamamen Ücretsiz (Karmaşık)
Bütçe kısıtlıysa aşağıdaki "Hibrit" model kullanılabilir:
- **Frontend:** Vercel (Ücretsiz)
- **Database:** Supabase (Ücretsiz tier)
- **Redis:** Upstash (Ücretsiz tier)
- **Backend/Worker:** Render veya Fly.io (Ücretsiz tier'lar kısıtlıdır, Tesseract kurulumu Dockerfile gerektirir).

---

## 4. Deployment Adım Adım Kontrol Listesi

1. [ ] **Veritabanı:** Supabase veya Railway üzerinde bir PostgreSQL veritabanı oluştur.
2. [ ] **Migration:** `alembic upgrade head` komutuyla tabloları oluştur.
3. [ ] **Redis:** Upstash veya Railway üzerinden Redis servisini hazırla.
4. [ ] **Docker:** Backend için `Dockerfile` oluştur (Tesseract ve Python bağımlılıklarını ekle).
5. [ ] **Deploy Backend:** Railway veya Render'a Docker üzerinden deploy et.
6. [ ] **Deploy Frontend:** Vercel'e deploy et ve `VITE_API_URL` değişkenini tanımla.
7. [ ] **OAuth:** Google Cloud Console'da "Authorized Redirect URIs" kısmına canlı domaini ekle.
8. [ ] **Test:** Kayıt ol, dosya yükle ve quiz oluşturma sürecini test et.

---

> [!WARNING]
> **Dosya Saklama Notu:** Sunucular (PaaS) geçici disk kullanır. `uploads/` klasörüne yüklenen dosyalar her deploy'da silinir. Kalıcı çözüm için AWS S3 veya Cloudflare R2 gibi bir nesne depolama servisi entegre edilmelidir.
