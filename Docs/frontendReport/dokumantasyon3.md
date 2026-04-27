# ExamAI Frontend ve Backend Entegrasyon Raporu

Bu rapor, ExamAI projesinde frontend (React) ve backend (FastAPI) sistemlerinin birbirlerine nasıl bağlandığını, Kategori, Dashboard sistemi ile eklenen "Sınav Silme" özelliğinin nasıl işlediğini açıklar.

## 1. Kategoriler Sistemi ve Veri Akışı

Sınav portalında gördüğünüz **Kategoriler** sekmesi, kullanıcı deneyimini hızlı kılabilmek adına tarayıcı önbelleği (LocalStorage) tabanlı hibrit bir modelle kurgulanmıştır. 
- Bu sayede veritabanı yorulmaz, ekstra bir backend endpoint'i beklemeden 0 milisaniyede tüm sınavlar istenilen kategorilere sürüklenir. Sınavları görüntülemek için ise ilgili satıra tıklandığında `navigate('/quiz/:quizId')` tetiklenerek sınav çözme/detay ekranına geçilir.

## 2. Temel Endpoint (API) Entegrasyon Haritası

Frontend uygulamasının Backend sistemi ile haberleştiği ana modüller ve uç noktaları aşağıda gruplandırılmıştır:

### A. Auth & Kullanıcı Bilgileri
- **Giriş / Kayıt:** `/api/v1/auth/register` ve `/api/v1/auth/login`
- **Google OAuth:** `http://localhost:8001/api/v1/auth/google/callback`

### B. Otomatik Sistemler (OCR & Arka Plan)
- **Kaynak (Not) Yükleme:** Frontend, belgeleri **`POST /api/v1/notes`** adresine gönderir. OCR Tesseract/PyMuPDF üzerinden CMD ile işlenir.

### C. Yapay Zeka AI Sınav & Değerlendirme Algoritması
1. **Sınav Başlatma (`POST /api/v1/quizzes`):** Frontend Modelında soru sayısı ve AI Payload uyumlaştırması yapılarak gönderilir.
2. **Asenkron AI Poll (`GET /api/v1/quizzes/{id}/status`):** Celery worker üzerinden her 5 saniyede bir dinlenir. Bekleme süresi kaynağın boyutuna göre 5 ila 30 saniye arasında değişir.
3. **Sınava Giriş:** Sayfa otomatik **`GET /api/v1/quizzes/{quiz_id}/questions`** adresinden soruları çeker (Cevaplar hileye karşı backendde gizlidir).
4. **Klasik Değerlendirme (Gemini API):** Sınav submit edildiğinde (`/submit`) test soruları standart olarak okunurken, açık uçlulara özel rubric yardımıyla 0-100 arasında Gemini skor hesaplar ve açıklama yazar.
5. **Sonuç Raporu:** **`GET /api/v1/quizzes/{quiz_id}/grading/{grading_id}`** adresinden çekilir.

## 3. Sınav Ayarları (Özelleştirilebilir Sınav Tipi)

Arayüzdeki **"Yeni Sınav Oluştur"** panelinde Payload (İstek gövdesi) uyuşmazlığını gidermek üzere tasarlanmış yapı şu şekilde çalışır:
- **Soru Sayısı (`total_questions`):** API'de 5 ile 50 arası desteklenir.
- **Sınav Türü (`mc_ratio`):** "Sadece Test" (1.0), "Sadece Klasik" (0.0).
- **Zorluk Seviyesi (`difficulty`):** easy, medium, hard.

## 4. Sınav Yönetimi ve Silme Modülü
Yeni eklenen özellikle birlikte sınavlar kalıcı olarak veritabanından silinebilir.

- **Frontend Akışı:** Dashboard Geşmiş (History) sekmesindeki listelerde veya Kategoriler ekranının en sağında (Çöp Kutusu ikonunda) kullanıcı sil tetiklemesi yapar. Onaylanırsa (`window.confirm`) API ile haberleşilir.
- **Backend Entegrasyon (`DELETE /api/v1/quizzes/{quiz_id}`):** Bu Endpoint FastAPI'da router olarak yazılmıştır. Çalıştırıldığında SQLAlchemy cascade mimarisi gereği o sınava ait tüm:
   - Sorular
   - Verilmiş Cevaplar
   - Yapay Zeka Karne ve Raporları (GradingSession)
Veritabanından kalıcı olarak temizlenir. Frontend üzerinde React filter metodu ile cihaz ekranından anında görsel efektle düşürülür.

**Dokümantasyon Sürümü:** 1.0.3
**Düzenleyen:** ExamAI System Agent
