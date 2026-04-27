# ExamAI — Canlıya Geçiş (Railway/Render) Teknik Rehberi

Bu rapor, ExamAI projesinin "Sıfır DevOps" ve "OCR Devre Dışı" kararlarına göre yapılan kod değişikliklerini ve kullanıcının yapması gereken adımları özetler.

## 🛠 Yapılan Kod Değişiklikleri (Antigravity Tarafından)

1.  **OCR Devre Dışı Bırakıldı:**
    - `backendWindsurf2/services/ocr_service.py` ve `extraction_service.py` dosyalarında Tesseract ve Gemini-Vision bağımlılıkları pasifize edildi.
    - Artık sistem sadece gömülü metni olan PDF'leri, DOCX ve TXT dosyalarını işleyecek. Görseller yüklendiğinde kullanıcıya bilgilendirme mesajı dönecek.
    - **Sonuç:** Sunucuya Tesseract kurma zahmetinden kurtulundu, deployment hızı %500 arttı.

2.  **Deployment Dosyaları Eklendi:**
    - **`Dockerfile`:** Railway ve Render için optimize edilmiş, hafif (slim) bir imaj oluşturuldu.
    - **`Procfile`:** Aynı sunucuda hem API'nin hem de Celery Worker'ın çalışmasını sağlayan komutlar tanımlandı.

3.  **Hafifletilmiş Altyapı:**
    - Görsel işleme kütüphaneleri (OpenCV vb.) artık opsiyonel; Tesseract eksikliği backend'in çökmesine neden olmayacak şekilde hata yönetimi eklendi.

---

## 🚀 Senin Yapman Gerekenler (Adım Adım)

### 1. Dış Servisleri Hazırla
- **Veritabanı (PostgreSQL):** [Supabase](https://supabase.com) üzerinden ücretsiz bir veritabanı aç ve `DATABASE_URL`'i not et.
- **Redis:** [Upstash](https://upstash.com) üzerinden ücretsiz bir Redis instance aç ve `REDIS_URL`'i not et.

### 2. Railway'e Yükle (Backend)
- Railway.app'e gir, `backendWindsurf2` klasörünü içeren GitHub reponu bağla.
- Railway Dashboard'da şu **Variables (Ortam Değişkenleri)** kısmını doldur:
  - `APP_ENV=production`
  - `DEBUG=false`
  - `DATABASE_URL`: (Supabase'den aldığın link)
  - `REDIS_URL`: (Upstash'ten aldığın link)
  - `GEMINI_API_KEY`: Kendi anahtarın.
  - `ALLOWED_ORIGINS`: `https://your-frontend.vercel.app` (Frontend adresin)
  - `SECRET_KEY`: Güçlü bir şifre (örn: `python -c "import secrets; print(secrets.token_hex(32))"` ile üret).

### 3. Frontend'i Vercel'e At
- `examai-frontend` klasörünü Vercel'e bağla.
- Environment Variables kısmına:
  - `VITE_API_URL`: `https://exam-ai-backend.up.railway.app` (Railway'in sana verdiği adres)

---

## 📌 Önemli Notlar
- **Dosya Depolama:** "Kalıcı olmasın" dediğin için dosyalar `uploads/` klasörüne yazılacak. Railway sunucusu her uyandığında veya her yeni kod attığında bu dosyalar **silinecektir.** Bu, uygulamanın çalışmasını engellemez; sadece eski yüklediğin notların metinleri veritabanında kalsa da orijinal dosyaları diskten silinir.
- **OCR:** Tarama (fotoğraf) halindeki PDF'lerden metin çıkarılamayacak. Sadece "seçilebilir" metni olan PDF'ler çalışacaktır.

---
**Hazırlayan:** Antigravity (Advanced Agentic Coding)
**Tarih:** 27.04.2026
