# ExamAI Frontend ve Backend Entegrasyon Raporu

Bu rapor, ExamAI projesinde frontend (React) ve backend (FastAPI) sistemlerinin birbirlerine nasıl bağlandığını, Kategori ve Dashboard sisteminin nasıl işlediğini ve sınav çözme sürecini teknik detaylarıyla açıklar.

## 1. Kategoriler Sistemi ve Veri Akışı

Sınav portalında gördüğünüz **Kategoriler** sekmesi, kullanıcı deneyimini hızlı kılabilmek adına tarayıcı önbelleği (LocalStorage) tabanlı hibrit bir modelle kurgulanmıştır. 

### Çalışma Mantığı
1. Kullanıcı `Kategoriler` veya `Oluşturulan Sınav` düğmelerine tıkladığında `Dashboard.jsx` rotayı keserek (Crash önlemi dahil edilmiş haliyle) ekrana `QuizCategories.jsx` bileşenini basmaktadır.
2. Bu bileşen backend'den listelenmiş ham sınavları (API Call: `GET /api/v1/quizzes`) alır. 
3. Dosya (`QuizCategories.jsx`) arka planda cihazın yerel önbellek (LocalStorage) deposunda iki adet kayıt tutar:
   - `quizCategories`: Kullanıcının oluşturduğu özel isimli kategori klasörlerinin listesi.
   - `quizToCategories`: Hangi sınav referansının (`quiz.id`) hangi kategoriye (`categoryId`) ait olduğunun haritası.
4. Bu sistem sayesinde veritabanı yorulmaz, ekstra bir backend endpoint'i beklemeden 0 milisaniyede tüm sınavlar istenilen kategorilere sürüklenir. Sınavları görüntülemek için ise ilgili satıra tıklandığında `navigate('/quiz/:quizId')` tetiklenerek sınav çözme/detay ekranına geçilir.

## 2. Temel Endpoint (API) Entegrasyon Haritası

Frontend uygulamasının Backend sistemi ile haberleştiği ana modüller ve uç noktaları aşağıda gruplandırılmıştır:

### A. Auth & Kullanıcı Bilgileri
- **Giriş / Kayıt:** `/api/v1/auth/register`, `/api/v1/auth/login`
- **Profil Bilgisi (Token):** `/api/v1/auth/me`
- **Google OAuth (Düzenlenmiş Port İle):** Tarayıcı Google Console üzerinden `http://localhost:8000/api/v1/auth/google/callback` adresiyle haberleşerek dönüş yapar ve frontend'e token bırakır.

### B. Otomatik Sistemler (OCR & Arka Plan)
- **Kaynak (Not) Yükleme:** Frontend'deki uploader bileşeni dosyaları **`POST /api/v1/notes`** adresine gönderir. Backend asenkron olarak OCR kütüphanesini (Tesseract / PyMuPDF) CMD üzerinden Portable bir mantıkla okutur, şifreler (Cipher) ve Postgres veritabanına korunaklı yazar.

### C. Yapay Zeka AI Sınav & Değerlendirme Algoritması
1. **Sınav Başlatma:** Frontend Modalında soru sayısı, test/klasik seçimi yapılır ve **`POST /api/v1/quizzes`** adresine tetiklenir.
2. **Asenkron AI Poll:** Sınavın oluşturulması vakit alacağı için Celery worker devreye girer. Frontend 5 saniyede bir **`GET /api/v1/quizzes/{quiz_id}/status`** endpointini dinler (Polling). Durum `processing`'den `ready`'ye geçince ekranda bildirim yanar.
   - **`mc_ratio` = `1.0`** olarak iletilir. Yapay zeka tüm soruları JSON formatında Test (Şıklı) olarak hazırlamaya zorlanır.
   - Eğer "Sadece Klasik" seçilirse `mc_ratio = 0.0` iletilir ve AI tüm soruları açık uçlu hazırlayıp rubrik (puanlama kriteri) kurgular.
4. **Klasik Soru Hesaplaması (Gemini API):** Öğrenci sınavı submit ettiğinde (`POST /api/v1/quizzes/{quiz_id}/submit`) test soruları backend'e gömülü idlerle milisaniyede algoritmik olarak çarpışıp hesaplanırken; Klasik (açık uçlu) sorular **Gemini API**'a servis (`ai_service.py`) üzerinden gönderilir.
   - Yapay zeka orjinal kaynak notları bağlam olarak okur.
   - Kendi kurguladığı rubrik (değerlendirme kriteri) üzerinden öğrencinin verdiği açık uçlu cevabı 0-100 arası puanlar ve neden puan kırdığına dair bir feedback yazar.
5. **Sonuç Raporlama:** Tüm işlemler tamamlandığında **`GET /api/v1/quizzes/{quiz_id}/grading/{grading_id}`** adresinden toplam yüzde/puan ve soru başına detaylı feedback/açıklamalar çekilerek ekrana (yeşil/kırmızı/sarı kartlar halinde) renkli şekilde bastırılır.

## 3. Sınav Ayarları (Özelleştirilebilir Sınav Tipi)

Arayüzdeki **"Yeni Sınav Oluştur"** panelinde öğrenci/öğretmen sınava ince ayarlar çekebilir ve Payload (İstek gövdesi) uyuşmazlığını gidermek üzere tasarlanmış yapı şu şekilde çalışır:

- **Soru Sayısı (`total_questions`):** API'de 5 ile 50 arası (default 10) desteklenir.
- **Sınav Türü (`mc_ratio`):**
  - Butonlar arası seçim olarak çalışır. "Sadece Test" tıklandığında oran `100` olur ve JSON'da `1.0` olarak convert edilir. "Sadece Klasik" için oran `0.0` gönderilir. 
  - (Eski halinde slider ile %70 girildiği bir modül vardı fakat revize edilip tamamen Test veya tamamen Klasik olarak 2 kutucuğa indirgenmiştir).
- **Zorluk Seviyesi (`difficulty`):** `easy`, `medium`, `hard` olarak seçilir ve `ai_service.py` içinde Prompt komutu içine dinamik yerleştirilir (*"All questions should be easy difficulty level"*).

**Dokümantasyon Sürümü:** 1.0.2
**Düzenleyen:** ExamAI System Agent
