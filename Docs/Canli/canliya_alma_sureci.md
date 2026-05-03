# 🚀 ExamAI Canlıya Alma ve Dağıtım Dökümantasyonu

Bu döküman, **Özgür Kotbaş** tarafından geliştirilen **ExamAI** projesinin yerel geliştirme ortamından bulut sunucularına (Fly.io ve Vercel) taşınma sürecini ve bu süreçte karşılaşılan teknik zorlukların çözümlerini kayıt altına almak için oluşturulmuştur.

## 🏗️ Kullanılan Teknolojiler ve Platformlar

| Bileşen | Platform / Teknoloji | Açıklama |
| :--- | :--- | :--- |
| **Backend (Beyin)** | **Fly.io** | FastAPI ve Celery işçilerini barındıran ana sunucu. |
| **Frontend (Arayüz)** | **Vercel** | Vite/React tabanlı kullanıcı arayüzü. |
| **Veritabanı** | **Supabase** | PostgreSQL bulut veritabanı servisi. |
| **Mesaj Kuyruğu** | **Upstash** | Celery görevleri için kullanılan Redis servisi. |
| **Yapay Zeka** | **Gemini 1.5 Flash** | Sınav kağıdı analizi ve soru üretimi için kullanılan ana motor. |

---

## 🛠️ Dağıtım Süreci ve Teknik Çözümler

### 1. Backend Yapılandırması (Fly.io)
Backend'in yayına alınması sürecinde Frankfurt (`fra`) bölgesi kullanılmış ve çoklu işlem (multi-process) mimarisi yapılandırılmıştır.

*   **Secrets Yönetimi:** `fly secrets set` komutu ile `DATABASE_URL`, `REDIS_URL` ve API anahtarları sisteme güvenli bir şekilde tanımlanmıştır.
*   **İşlem Tanımları:** `fly.toml` dosyasında hem API (Uvicorn) hem de Worker (Celery) süreçleri aynı anda çalışacak şekilde yapılandırılmıştır.

### 2. Karşılaşılan Kritik Hatalar ve Çözüm Yolları

#### ❌ Port ve Bağlantı Sorunları (502 Bad Gateway)
*   **Analiz:** Fly.io'nun dış bağlantıları ile uygulamanın dinlediği iç portun (8080) uyuşmaması sonucu bağlantı reddedildi.
*   **Çözüm:** `fly.toml` dosyası `internal_port = 8080` olacak şekilde revize edildi ve trafik `app` sürecine yönlendirildi.

#### ❌ Veritabanı Sürücü Hataları (ModuleNotFoundError & Asyncio Error)
*   **Hata 1:** Sunucu imajında PostgreSQL ile iletişim kuracak `psycopg2` kütüphanesinin eksik olması.
*   **Hata 2:** SQLAlchemy asenkron motorunun senkron bir sürücü olan `psycopg2` ile çalışmayı reddetmesi.
*   **Çözüm:** `requirements.txt` dosyasına asenkron sürücü olan `asyncpg` eklendi. `DATABASE_URL` bağlantı protokolü `postgresql+asyncpg://` olarak güncellendi.

### 3. Frontend Yapılandırması (Vercel)
Frontend'in Backend ile uyumlu çalışması için Vercel üzerinde dağıtım yapılmıştır.

*   **API Bağlantısı:** Vercel Environment Variables kısmına `VITE_API_URL` olarak `https://backendwindsurf2.fly.dev` adresi tanımlanmıştır.
*   **CORS Ayarı:** Backend tarafında `ALLOWED_ORIGINS` değişkeni Vercel linkine izin verecek şekilde güncellenmiştir.

---

## 🔗 Entegrasyon Ayarları
*   **Google OAuth:** Kullanıcı girişlerinin çalışması için `GOOGLE_REDIRECT_URI` canlı backend adresi üzerinden yapılandırılmıştır.
*   **Güvenlik:** Sisteme sadece belirlenen frontend adresinden erişim sağlanması için CORS kısıtlamaları aktifleştirilmiştir.

---
*Bu döküman projenin 2026 Nisan ayı canlıya geçiş süreci baz alınarak hazırlanmıştır.*