# ExamAI Proje Analiz Raporu

**Hazırlayan:** Antigravity (Yazılım Mimarı & Kod Denetmeni)  
**Tarih:** 13 Nisan 2026  - 15.57
**Proje Adı:** ExamAI - AI Destekli Kişiselleştirilmiş Sınav Platformu

## Giriş
Bu rapor, "ExamAI" projesinin kod tabanının, başlangıçta planlanan proje taslağına ve teknik gereksinimlere uyumunu analiz etmek amacıyla hazırlanmıştır. Proje; öğrencilerin ders notlarından multimodal yapay zeka (Gemini 1.5 Flash) kullanarak kişiselleştirilmiş sınavlar üreten bir web uygulamasıdır.

---

## Bölüm 1: Altyapı, Veritabanı ve Güvenlik (İP1)

### 1. Backend ve Frontend Teknolojileri
*   **Backend:** FastAPI framework'ü kullanılarak `backendWindsurf2/main.py` dosyasında yapılandırılmıştır. Uvicorn sunucusu üzerinden asenkron bir yapıda çalışmaktadır.
*   **Frontend:** Vite tabanlı React uygulaması olarak `examai-frontend` klasöründe geliştirilmiştir (`package.json` satır 7 ve 39).
*   **Çevre Değişkenleri:** `.env` dosyası üzerinden API anahtarları (Gemini, HF, Redis vb.) ve DB bağlantıları yönetilmektedir. `config.py` içinde Pydantic BaseSettings ile okunmaktadır.

### 2. Kimlik Doğrulama (Google & JWT)
*   **Google Auth:** `backendWindsurf2/routers/auth.py` (satır 76-122) içinde Google OAuth akışı kurulmuştur. Kullanıcılar Google üzerinden giriş yapabilmektedir.
*   **JWT Token:** Kimlik doğrulama sonrasında `utils/security.py` üzerinden üretilen JWT (Access Token) dönülmektedir. 
*   **HTTP-only Cookie:** Kod incelemesinde token'ın gövde (body) ve URL parametresiyle taşındığı görülmüştür (`auth.py` satır 105). HTTP-only cookie tercihi opsiyonel bırakılmış, Bearer token mimarisi öncelendirilmiştir.

### 3. Veritabanı Şeması ve ORM
*   **ORM:** SQLAlchemy (Async) kullanılmıştır. `database.py` içinde `AsyncSession` yapılandırması mevcuttur.
*   **Veritabanı:** PostgreSQL entegrasyonu tamamlanmıştır (`docker-compose-infra.yml`).
*   **Tablolar:** `backendWindsurf2/models/` dizininde gereksinim duyulan tüm tablolar mevcuttur:
    *   `user.py`: Kullanıcı bilgileri.
    *   `note.py`: Yüklenen notlar.
    *   `question.py`: Üretilen sorular.
    *   `quiz.py`: Sınav oturumları.
    *   `answer.py`: Öğrenci cevapları.

### 4. Veri Şifreleme ve Yetkilendirme
*   **Şifreleme:** Not içerikleri veritabanında şifreli olarak saklanmaktadır. `models/note.py` (satır 25-26) içinde `raw_text_encrypted` ve `cleaned_text_encrypted` alanları AES-256-GCM (Fernet) ile korunmaktadır.
*   **Yetkilendirme:** API endpoint'lerinde (örneğin `routers/quiz.py` satır 45) `current_user.id` kontrolü yapılarak kullanıcıların sadece kendi verilerine erişmesi sağlanmaktadır.

---

## Bölüm 2: Görüntü İşleme ve Not Yönetimi (İP2)

### 5. Dosya Yükleme Arayüzü
*   **Kütüphane:** `react-dropzone` kullanılarak sürükle-bırak desteği sağlanmıştır (`FileUpload.jsx` satır 2).
*   **Önizleme:** Yüklenen dosyaların isim ve boyut bilgileri liste halinde sunulmaktadır.
*   **Resizing:** Frontend tarafında (JS tarafında) görsel boyutlandırma (1024x1024) mantığına rastlanmamıştır; dosyalar doğrudan backend'e gönderilmektedir.

### 6. Görsel Ön İşleme
*   `backendWindsurf2/services/ocr_service.py` (satır 24-72) içinde gelişmiş ön işleme teknikleri uygulanmıştır:
    *   **Grayscale:** `image.convert("L")`
    *   **CLAHE Contrast:** Kontrast artırma (OpenCV).
    *   **Gaussian Blur:** Gürültü azaltma.
    *   **Adaptive Threshold:** Binarizasyon.
*   **Açı Düzeltme:** Otomatik skew/deskew (açı düzeltme) mantığı kodda görülmemiştir.

### 7. OCR Stratejisi
*   Hybrid bir yapı kurulmuştur: `tesseract_gemini` varsayılan stratejidir (`ocr_service.py` satır 195).
*   Tesseract ile çıkarılan metin, Gemini AI kullanılarak `_gemini_cleanup` (satır 111-128) aşamasında temizlenmekte ve `Note` tablosuna kaydedilmektedir.

---

## Bölüm 3: Sınav Üretimi ve Token Optimizasyonu (İP3)

### 8. AI Prompt Mühendisliği
*   `backendWindsurf2/services/ai_service.py` (satır 241-305) içinde profesyonel prompt yapısı kurulmuştur.
*   **Test Soruları:** `multiple_choice` tipi için `options` ve `correct_answer` içeren JSON şeması zorunlu kılınmıştır.
*   **Açık Uçlu:** `open_ended` tipi için `rubric` ve `topic` içeren JSON çıktıları istenmektedir.

### 9. Kişiselleştirme Mantığı
*   `routers/quiz.py` (satır 78-111) içinde kullanıcının geçmişteki yanlışları (`Answer.score < 5`) sorgulanmaktadır.
*   Belirlenen "Zayıf Konular" (Weak Topics), yeni sınav üretimi sırasında AI prompt'una bir direktif olarak eklenmektedir (`ai_service.py` satır 267).

### 10. Token Optimizasyonu ve Önbellekleme
*   **Batch Üretim:** Tüm sorular tek bir AI isteğinde (bulk) üretilmektedir.
*   **Önbellekleme:** Redis tabanlı bir cache sistemi kurulmuştur. Aynı parametrelerle (not_id, soru sayısı, dil vb.) gelen istekler AI'ya gitmeden `cache_service.py` üzerinden Redis'ten döndürülmektedir (`routers/quiz.py` satır 114).

### 11. Asenkron Yapı ve Durum Güncellemesi
*   **Asenkronite:** Sınav üretimi Celery worker'lar üzerinden arka planda yürütülmektedir (`routers/quiz.py` satır 156).
*   **Frontend Senkronizasyon:** WebSocket/SSE yerine **Polling (5sn aralıklarla sorgulama)** yöntemi tercih edilmiştir (`Dashboard.jsx` satır 60).
*   **Backoff:** Gemini API limit aşımlarında (429) exponential backoff mekanizması `ai_service.py` (satır 336-353) içinde uygulanmıştır.

---

## Bölüm 4: Hibrid Puanlama ve Geri Bildirim (İP4)

### 12. Test Puanlaması (Backend)
*   Test (Multiple Choice) soruları için AI kullanılmadan doğrudan backend'de eşleşme kontrolü yapılmaktadır (`routers/quiz.py` satır 402-427). Sonuçlar `Answer` tablosuna anında işlenmektedir.

### 13. Açık Uçlu Puanlama (AI)
*   Açık uçlu cevaplar için Gemini'ye; soru, öğrenci cevabı ve ilgili ders notu içeriği (context) gönderilmektedir (`services/celery_tasks.py` satır 329-352).
*   AI'dan dönen 0-100 arası puan, soru ağırlığına göre normalize edilerek ve detaylı gerekçeli geri bildirimle birlikte kaydedilmektedir.

### 14. Konu Etiketleme (Topic Tagging)
*   Sınav üretimi sırasında AI her soruyu bir konuya (topic) atamakta ve bu bilgi veritabanına kaydedilmektedir (`ai_service.py` satır 292).

### 15. Analitik Raporlar
*   **Backend:** `/quizzes/analytics` endpoint'i üzerinden konu bazlı başarı oranları hesaplanmaktadır.
*   **Frontend:** `Dashboard.jsx` (satır 551-659) içinde Recharts kütüphanesi (progress-bar simülasyonu) kullanılarak görsel raporlar sunulmaktadır. Zayıf ve güçlü konular kullanıcıya raporlanmaktadır.

---

## Bölüm 5: Test, Mimari ve Diğer Standartlar (İP5)

### 16. Validasyon ve Fallback
*   API seviyesinde Pydantic şemaları (`schemas/`) ile girdi doğrulama yapılmaktadır.
*   AI'dan dönen JSON çıktıları regex ile ayıklanmakta ve hatalı format durumunda fallback (boş liste veya hata yönetimi) uygulanmaktadır.

### 17. Frontend Mimarisi
*   **State Yönetimi:** @tanstack/react-query kullanılmaktadır (`package.json` satır 14).
*   **Formlar:** React Hook Form + Zod validasyonu uygulanmıştır.
*   **Stil:** TailwindCSS kullanılarak modern ve responsive bir arayüz tasarlanmıştır.

### 18. API Dokümantasyonu ve Anonimleştirme
*   **Swagger:** `/docs` adresinde FastAPI üzerinden Swagger UI aktiftir (`main.py` satır 55).
*   **Anonimleştirme:** AI servisine gönderilen verilerde henüz otomatik bir anonimleştirme (maskeleme) filtresine rastlanmamıştır.

### 19. Testler
*   **Backend:** `Pytest` ile yazılmış temel birim testleri mevcuttur (`backendWindsurf2/tests/`).
*   **Frontend:** `Jest` veya `Cypress` gibi frontend test araçlarının yapılandırması henüz tamamlanmamıştır.

---

## Geliştirilecek Alanlar (Öneriler)
1.  **Frontend Resizing:** Kullanıcıların yüksek çözünürlüklü görsellerini yüklemeden önce tarayıcıda boyutlandırmak, sunucu yükünü ve bandwidth kullanımını azaltacaktır.
2.  **WebSocket Geçişi:** Mevcut Polling (sorgulama) yöntemi yerine WebSocket kullanılarak daha "real-time" bir deneyim sağlanabilir.
3.  **Frontend Testleri:** Uygulamanın kararlılığı için bileşen bazlı (unit) ve uçtan uca (E2E) testlerin eklenmesi önerilir.
4.  **Veri Maskeleme:** AI tarafına gönderilen not içeriklerinde hassas verilerin (isim, e-posta vb.) maskelenmesi güvenlik standartlarını artıracaktır.

---
**Sonuç:** ExamAI projesi, teknik altyapı ve AI entegrasyonu açısından son derece sağlam temellere oturmaktadır. Özellikle kişiselleştirme (zayıf konu analizi) ve hibrit puanlama özellikleri, projeyi piyasadaki rakip çözümlerden ayırmaktadır.
