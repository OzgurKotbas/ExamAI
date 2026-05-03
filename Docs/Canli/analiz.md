# ExamAI Proje Analiz ve Dökümantasyonu

Bu döküman, ExamAI platformunun teknik mimarisini, dosya yapısını, çalışma süreçlerini ve kullanılan teknolojileri özetlemektedir.

## 1. Proje Genel Bakış
ExamAI, kullanıcıların ders notlarını (PDF veya metin) yükleyerek yapay zeka desteğiyle kişiselleştirilmiş sınavlar oluşturmasını ve bu sınavların otomatik olarak değerlendirilmesini sağlayan bir platformdur.

---

## 2. Dosya Yapısı ve Görevleri

### 📂 Backend (FastAPI - `backendWindsurf2`)
Backend, asenkron yapıda çalışan bir FastAPI uygulamasıdır.
- **`main.py`**: Uygulamanın giriş noktası, middleware ve router tanımlamaları.
- **`routers/`**: API uç noktaları.
    - `quiz.py`: Sınav oluşturma, getirme, cevaplama ve puanlama işlemleri.
    - `notes.py`: Not yükleme, metin çıkarma ve şifreleme.
    - `auth.py`: Kullanıcı kayıt, giriş ve oturum yönetimi.
- **`services/`**: İş mantığı (Business Logic).
    - `ai_service.py`: Hugging Face ve Gemini API entegrasyonu, prompt mühendisliği.
    - `celery_tasks.py`: Uzun süren işlemlerin (sınav üretimi, AI değerlendirme) arka planda çalıştırılması.
    - `extraction_service.py`: PDF'lerden metin çıkarma.
    - `ocr_service.py`: Taranmış dökümanlar için OCR (Görüntü İşleme).
- **`models/`**: Veritabanı tabloları (SQLAlchemy).
- **`utils/`**: Güvenlik (AES şifreleme), lokalizasyon ve yardımcı fonksiyonlar.

### 📂 Frontend (React - `examai-frontend`)
Modern ve dinamik bir React arayüzü.
- **`src/pages/`**: Temel sayfalar.
    - `Dashboard.jsx`: Notların listelendiği, yeni sınav başlatılan ana ekran.
    - `Quiz.jsx`: Sınavın çözüldüğü interaktif alan.
    - `AuthCallback.jsx`: OAuth ve oturum yönlendirmeleri.
- **`src/components/`**: Tekrar kullanılabilir bileşenler.
    - `FileUpload.jsx`: Sürükle-bırak destekli not yükleme modülü.
    - `QuizCategories.jsx`: Sınav türü ve zorluk seçimi.
- **`src/api/`**: Axios tabanlı backend istekleri.

---

## 3. Bağlantılar ve Mimari

ExamAI "Decoupled" (Ayrık) bir mimari kullanır:
1.  **Frontend <-> Backend**: REST API üzerinden haberleşir.
2.  **Backend <-> Celery**: Redis aracılığıyla mesaj kuyruğu yönetilir.
3.  **Backend <-> Veritabanı**: Supabase (PostgreSQL) üzerinde tüm veriler saklanır.
4.  **Backend <-> AI**: Hugging Face Router üzerinden Qwen, Mistral gibi modeller kullanılır; hata durumunda Gemini API'ye otomatik geçiş (fallback) yapılır.

---

## 4. Sınav Oluşturma Süreci

1.  **Not İşleme**: Kullanıcı not yüklediğinde, metin çıkarılır ve AES-256 ile şifrelenerek kaydedilir.
2.  **Kişiselleştirme**: Sistem, kullanıcının geçmiş sınavlarını analiz ederek düşük puan aldığı konuları ("Zayıf Konular") belirler.
3.  **Prompt Üretimi**: `ai_service.py` içinde; notun içeriği, zayıf konular, zorluk seviyesi ve dil tercihi (TR/EN) birleştirilerek AI'ya özel bir talimat gönderilir.
4.  **Arka Plan Çalışması**: Sınav üretimi asenkron bir Celery taskı olarak başlatılır. Kullanıcıya hemen "hazırlanıyor" yanıtı döner.
5.  **Cache Mekanizması**: Aynı nottan aynı parametrelerle sınav istenirse, Redis üzerinden anında eski sınav döner (Maliyet ve hız tasarrufu).

---

## 5. Değerlendirme (Grading) Süreci

Platform iki farklı değerlendirme motoru kullanır:
- **Otomatik Değerlendirme**: Çoktan seçmeli sorular için backend tarafında anında kontrol yapılır.
- **AI Değerlendirme (Açık Uçlu)**: 
    1. Kullanıcının cevabı asenkron bir taska gönderilir.
    2. AI'ya sorunun metni, öğrencinin cevabı ve notun **en ilgili bölümleri** (keyword matching ile seçilir) gönderilir.
    3. AI; puan (0-100), geri bildirim, eksik noktalar ve iyileştirme önerileri sunar.

---

## 6. Kullanılan API ve Teknolojiler

- **Backend**: FastAPI, SQLAlchemy, Alembic, Celery.
- **Frontend**: React, Vite, Tailwind CSS (isteğe bağlı), Framer Motion (animasyon).
- **Veritabanı & Auth**: Supabase (PostgreSQL), Redis.
- **AI Modelleri**: 
    - **Hugging Face Router**: Qwen-72B, Mistral-Nemo (Öncelikli).
    - **Google Gemini**: Fallback (Yedek) ve karmaşık grading işlemleri için.
- **Güvenlik**: AES-256 Encryption (Kullanıcı notları veritabanında okunamaz halde saklanır).

---

## 7. Atlanan / Dikkat Edilmesi Gereken Konular

- **Rate Limiting**: AI servislerinde (HF/Gemini) kota dolumuna karşı "Exponential Backoff" (Hata durumunda bekleme süresini artırarak tekrar deneme) mekanizması eklenmiştir.
- **Vektör Arama (Opsiyonel Gelişim)**: Şu an grading için basit keyword matching kullanılmaktadır. Gelecekte daha hassas sonuçlar için RAG (Retrieval-Augmented Generation) mimarisine geçilebilir.
- **Multi-Language**: Uygulama uçtan uca TR ve EN desteği sunar, AI çıktıları seçilen dile göre zorunlu tutulur.
