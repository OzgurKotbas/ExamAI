# ExamAI Frontend - Backend Entegrasyonu ve İşleyiş Raporu

Bu rapor ExamAI projesindeki Frontend (React/Vite) ve Backend (FastAPI) sistemleri arasındaki bağlantı noktalarını, veri akışını, yapay zeka entegrasyonu aşamalarını ve özellikle farklı işletim sistemlerinde sorunsuz çalışması için yapılan taşınabilir (portable) OCR (Tesseract) mimarisini açıklar.

## 1. Frontend - Backend Endpoint (Uç Nokta) Haritası

Frontend uygulamasındaki (`src/api/index.js`) metodlar, backend üzerindeki (örn: `backendWindsurf2/routers/`) mevcut rotalara aşağıda belirtilen şekilde bağlanmıştır.

### A. Kimlik Doğrulama (Auth) Rotası
- **Kişisel Bilgiler & Tokenlar**
  - **FE Call:** `authApi.register(data)` ➔ **BE Route:** `POST /api/v1/auth/register`
  - **FE Call:** `authApi.login(email, pwd)` ➔ **BE Route:** `POST /api/v1/auth/login` (Zorunlu `multipart/form-data`)
  - **FE Call:** `authApi.me()` ➔ **BE Route:** `GET /api/v1/auth/me` (Token ile korunan kullanıcı bilgisi çekimi)

### B. Not Yükleme ve OCR Akışı
Kullanıcıların `.pdf`, `.docx`, `.txt` veya görsel formattaki verilerini backend tarafına yollayıp metne dönüştürülmesini tetiklediği süreçtir.
- **Frontend Bileşeni:** `components/FileUpload.jsx`
- **FE Call:** `notesApi.upload(files)` ➔ **BE Route:** `POST /api/v1/notes`
- **BE İşleyiş:** Çoklu dosya alır. `extraction_service.py` dosya tiplerini algılar. Görseller ve Taranmış PDF'ler için `pytesseract` çalıştırılır. İşlenen ham ve temizlenip şifrelenmiş metin `Note` tablosuna saklanır.
- **FE Call:** `notesApi.list()` ➔ **BE Route:** `GET /api/v1/notes` (Dashboard sekmesinde listeleme)

### C. Yapay Zeka ile Sınav (Quiz) Oluşturma Rotası
- **Frontend Bileşeni:** `components/FileUpload.jsx` içerisindeki Quiz Modal'ı.
- **FE Call:** `quizzesApi.create(data)` ➔ **BE Route:** `POST /api/v1/quizzes` (Sınav oluşturma görevi asenkron olarak (Celery) alınır, durumu `pending` işaretlenir.)
- **FE Call:** `quizzesApi.getStatus(quizId)` ➔ **BE Route:** `GET /api/v1/quizzes/{quizId}/status` (Frontend 5 saniyede bir polling yaparak Celery task'ın bitip bitmediğini denetler.)
- **FE Call:** `quizzesApi.list()` ➔ **BE Route:** `GET /api/v1/quizzes` (Quiz geçmişini veya "Kategoriler" sayfasını besler.)

### D. Sınavı Çözme ve Değerlendirme Rotası (YENİ - Quiz.jsx Sayfası)
Öğrencinin sınava girmesi, açık uçlu / çoktan seçmeli soruları yanıtlayarak Gemini AI'ya değerlendirtmesi sürecidir.
- **Frontend Bileşeni:** `pages/Quiz.jsx` (Dinamik route: `/quiz/:quizId`)
- **FE Call:** `quizzesApi.getQuestions(quizId)` ➔ **BE Route:** `GET /api/v1/quizzes/{quizId}/questions` (Doğru cevaplar haricinde sadece soru köklerini ve test seçeneklerini çeker.)
- **FE Call:** `quizzesApi.submit(quizId, answers)` ➔ **BE Route:** `POST /api/v1/quizzes/{quizId}/submit`
- **BE İşleyiş:** Çoktan seçmeli sorular için anlık 0 ya da 100 olarak doğru/yanlış atanır. "Açık uçlu (Klasik)" sorular ise öğrencinin orijinal notlarıyla (Context) birlikte Gemini AI'a iletilir. AI 0-100 arası notunu ve string formatında Feedeback'ini oluşturur.
- **FE Puan Polling:** `quizzesApi.getGradingStatus(quizId, gradingId)` ➔ **BE Route:** `GET /api/v1/quizzes/{quizId}/grading/{gradingId}/status` (AI değerlendirmesinin bitmesi beklenir.)
- **FE Call:** `quizzesApi.getResults(quizId, gradingId)` ➔ **BE Route:** `GET /api/v1/quizzes/{quizId}/grading/{gradingId}` (Tüm sınav başarı puanı, yüzdesi ve her soru başına detaylı feedback/geri dönüş raporu ekrana yansıtılır.)

---

## 2. Taşınabilir (Portable) OCR (Tesseract) Çözümü

Önceki aşamada `subprocess` ve `Powershell` taraflı hatalar görülmesi üzerine, Windows/Linux/Mac arasında tesseract executable (çalıştırılabilir dosya) sorunları çıktığı tespit edildi. Bunu çözmek adına backend tarafı (`ocr_service.py` ve `extraction_service.py`) aşağıdaki yaklaşımla güncellenmiştir:

1. **Python `shutil.which` Tespiti:** Sistem ilk olarak `shutil.which("tesseract")` modülünü çalıştırır. Eğer kullanıcı bilgisayarına veya kurulu Linux ortamına (`C:\Program Files\Tesseract-OCR\tesseract.exe` veya `/usr/bin/tesseract` gibi) PATH yapılandırmasını düzgün yaptıysa tesseract adresi saptanır. Çıkan sonuç Pytesseract'ın iç yapılandırmasına (`pytesseract.tesseract_cmd`) atanır. Böylece sub-process olarak cmd veya bash otomatik çözülür. PowerShell override edilmesine gerek kalmaz.
2. **.env Tesseract Fallback:** Farklı lokasyonlara Tesseract kuran ve PATH'e (ortam değişkenlerine) eklemekle uğraşmak istemeyen geliştiriciler/sunucular, proje ana dizinindeki `.env` dosyasına `TESSERACT_CMD_PATH=C:\Custom-Path\tesseract.exe` satırını yazarak sorunu çözerler.

### Docker Tesseract Kurulum Yapısı
Bu uygulama farklı bir cihaza, örneğin Railway veya bir bulut servisine taşındığında (Docker kullanarak Container içine alındığında) tesseract tamamen evrensel hale gelir. İşletim sistemi kalıntılarına takılmaz. 

*Detaylar ve kurulum senaryosu proje geliştiricisine ayrıntılı olarak sunulmuştur.*

## Özeti ve Süreç Akışı
1. Kullanıcı Ders Notunu atar. ➔ OCR dinamik/portable yoldan okur. ➔ Temizlenmiş Metin DB'ye yazılır.
2. Kullanıcı "Quiz Hazırla" der. ➔ Celery Asenkron işlemi arka planda Gemini promptunu (Zorluk, Oran vs. dikkate alarak) hazırlar. AI'dan sınav döner.
3. Kullanıcı "Quiz Görüntüle / Çöz" butonuna basar. Testi çözer. Tüm cevaplar (`submit`) backend'e iletilir.
4. Backend testleri anında puanlarken açık uçluları tekrar AI'ya (Gemini) yorumlatır.
5. Kullanıcı Sınav Puanını ve Detaylı AI Açıklamalarını görür.

**Dokümantasyon Sürümü:** 1.0.0
**Oluşturan:** ExamAI Agent
