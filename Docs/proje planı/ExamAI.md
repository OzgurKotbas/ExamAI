# [cite_start]Proje Tanımı [cite: 1]

[cite_start]ExamAl, öğrencilerin ders notlarından (resim dosyası, PDF, metin) multimodal yapay zekâ (Gemni 1.5 Flash) yardımıyla kişiselleştirilmiş sınavlar üreten bir web uygulamasıdır. [cite: 2] [cite_start]Kişiselleştirme öğrencinin geçmiş performansına (yanlış yaptığı konular, zorluk seviyesi) göre soru seçimi ve seviye ayarı yapılarak sağlanır. [cite: 3] [cite_start]Token maliyeti düşük tutulmak için test sorularının değerlendirilmesi backend tarafında otomatik yapılır; [cite: 4] [cite_start]Al sadece açık uçlu soruların semantik değerlendirmesini ve puanlamasını gerçekleştirir. [cite: 5] [cite_start]Ayrıca aynı not ve aynı parametrelerle daha önce üretilmiş sınavlar önbellekten getirilerek gereksiz API çağrıları engellenir. [cite: 6]

## [cite_start]Süreç Akışı [cite: 7]

### [cite_start]1. Görüntü İşleme ve Metin Çıkarma [cite: 8]
* [cite_start]Kullanıcı, ders notlarını dosya yükleme yoluyla (resim dosyası, PDF) web uygulamasına ekler. [cite: 9]
* [cite_start]Yüklenen dosya backend'e gönderilir. [cite: 10]
* [cite_start]Görsel ön işleme (kontrast, gürültü azaltma) uygulanır. [cite: 11]
* [cite_start]Önce Tesseract/Google Cloud Vision ile OCR yapılır, ardından Gemini (veya farklı bir ücretsiz model ile) ile metin düzenlenir (karar test aşamasında verilecek). [cite: 12]
* [cite_start]Çıkarılan metin `context_id` ile ilişkilendirilerek kaydedilir. [cite: 13]

### [cite_start]2. Kişiselleştirilmiş Sınav Üretimi [cite: 14]
* [cite_start]Kullanıcı; soru sayısı, test/açık uçlu oranı, zorluk seviyesi gibi tercihleri belirler. [cite: 15]
* [cite_start]Backend, geçmiş yanlışlarını da dikkate alarak bir prompt oluşturur. [cite: 16]
* [cite_start]Al'dan hem test (cevap anahtarıyla birlikte) hem açık uçlu soruları yapılandırılmış JSON formatında üretmesi istenir. [cite: 17]
* [cite_start]Üretim asenkron olarak yapılır, kullanıcıya bildirim gönderilir. [cite: 18]

### [cite_start]3. Hibrid Değerlendirme [cite: 19]
* [cite_start]**Test soruları:** Öğrencinin işaretlediği şık, veritabanındaki doğru cevapla karşılaştırılarak anında puanlanır (Al kullanılmaz). [cite: 20]
* [cite_start]**Açık uçlu sorular:** Öğrencinin metin cevabı, ilgili soru ve not içeriğiyle birlikte Al'ya gönderilir. [cite: 21] [cite_start]Al, puanlama kriterlerine (anahtar kelimeler, akıl yürütme) göre 0-100 arası puan ve gerekçeli geri bildirim üretir. [cite: 22]

### [cite_start]4. Analitik Rapor ve Gelişim Takibi [cite: 23]
* Toplam puan, konu bazında doğruluk yüzdeleri, yanlış yapılan konular grafiklerle gösterilir. [cite_start]Konu etiketleri soru üretimi sırasında Al tarafından eklenir. [cite: 24]

---

## [cite_start]İş Paketleri ve Görevler [cite: 25]

### [cite_start]İP1: Altyapı, Veritabanı ve Güvenlik [cite: 26]

| Görev No | Açıklama |
| :--- | :--- |
| **1.1** | FastAPI backend ve React (Vite) frontend projelerinin başlatılması. [cite_start]Çevre değişkenleri (.env) ile yönetim. [cite: 27] |
| **1.2** | Google Authentication ile kullanıcı doğrulama sistemi. [cite_start]JWT token yönetimi. [cite: 27] |
| **1.3** | [cite_start]Veritabanı tasarımı: <br> - User tablosu (id, email, ad, şifre hash'i) <br> - Note tablosu (id, user_id, context_id, raw_text, cleaned_text, created_at) <br> - Question tablosu (id, quiz_id, type, text, correct_answer (test için), topic, difficulty, rubric (opsiyonel)) <br> - Quiz tablosu (id, user_id, note_id, created_at, parameters) <br> - Answer tablosu (id, user_id, question_id, user_answer, score, feedback, graded_at) <br> - İlişkiler ve indeksler oluşturulacak. [cite: 27] |
| **1.4** | [cite_start]Veri şifreleme (kullanıcı notları için) ve yetkilendirme kontrollerinin eklenmesi. [cite: 27] |

### [cite_start]İP2: Görüntü İşleme ve Not Yönetimi (OCR İyileştirmeleri) [cite: 28]

| Görev No | Açıklama |
| :--- | :--- |
| **2.1** | Dosya yükleme bileşeni: Kullanıcının resim (JPG, PNG) veya PDF dosyalarını yükleyebileceği bir arayüz. [cite_start]Sürükle-bırak desteği, dosya önizleme ve boyut kontrolü. [cite: 29] |
| **2.2** | [cite_start]Görsel ön işleme: OpenCV.js veya backend'de OpenCV ile kontrast artırma, gürültü azaltma, açı düzeltme (PDF sayfaları için ayrıştırma dahil). [cite: 29] |
| **2.3** | OCR stratejisi: <br> - Alternatif 1: Tesseract.js (client-side) veya Google Cloud Vision ile metin çıkar, ardından Gemini ile düzeltme. <br> - Alternatif 2: Doğrudan Gemini 1.5 Flash ile metin çıkar (test edilip karar verilecek). [cite_start]<br> Görevde her iki yöntemin test edilmesi ve doğruluk oranlarının karşılaştırılması yer alır. [cite: 29] |
| **2.4** | [cite_start]Çıkarılan metnin temizlenmesi (gereksiz boşluklar, sayfa numaraları vb.) ve Note tablosuna kaydedilmesi. [cite: 29] |
| **2.5** | [cite_start]Düşük kaliteli görsellerde kullanıcıyı uyarıp tekrar yükleme yapmasını sağlama. [cite: 29] |

### [cite_start]İP3: Kişiselleştirilmiş Sınav Üretimi ve Token Optimizasyonu [cite: 30]

| Görev No | Açıklama |
| :--- | :--- |
| **3.1** | Prompt mühendisliği: <br> - Al'dan test soruları için `{soru_metni, secenekler, dogru_cevap, konu, zorluk}` içeren JSON çıktısı alacak prompt hazırlanması. <br> - Açık uçlu sorular için `{soru_metni, konu, zorluk, rubric}` çıktısı. [cite_start]<br> Prompt içinde örnek çıktı formatları ve kısıtlamalar (örneğin soru sayısı, token sınırı) belirtilir. [cite: 31] |
| **3.2** | [cite_start]Kişiselleştirme mantığı: Kullanıcının geçmiş yanlışları (Answer tablosundan düşük puanlı konular) sorgulanarak prompt'a "bu konulardan daha fazla soru ekle" şeklinde yönlendirme eklenmesi. [cite: 31] |
| **3.3** | Token optimizasyonu: <br> - Uzun notlar için özet çıkarma (Gemini ile özetletme) ve özet üzerinden soru üretimi. <br> - Aynı not için test ve açık uçlu soruların tek bir promptla (batch) üretilmesi. [cite_start]<br> - Önbellekleme: (user_id, note_id, soru_sayisi, test_orani, zorluk) anahtarıyla daha önce üretilmiş quiz varsa doğrudan getirilmesi. [cite: 31] |
| **3.4** | Asenkron işlem: Celery veya FastAPI Background Tasks ile soru üretiminin arka planda çalışması. [cite_start]Kullanıcıya "Sınavınız hazırlanıyor, bildirim gelecek" mesajı ve WebSocket veya Server-Sent Events (SSE) ile durum güncellemeleri. [cite: 31] |
| **3.5** | [cite_start]Hata durumunda yeniden deneme mekanizması (exponential backoff) ve kullanıcıya anlaşılır hata mesajları. [cite: 31] |

### [cite_start]İP4: Hibrid Puanlama ve Geri Bildirim [cite: 32]

| Görev No | Açıklama |
| :--- | :--- |
| **4.1** | [cite_start]Test sorularının backend'de puanlanması: Kullanıcının cevabı ile `Question.correct_answer` karşılaştırılır, Answer tablosuna puan (0 veya 100) ve doğru/yanlış feedback'i yazılır. [cite: 33] |
| **4.2** | Açık uçlu puanlama modülü: <br> - Prompt: Soru, öğrenci cevabı, not içeriği (ve varsa rubric) verilerek 0-100 arası puan ve gerekçeli geri bildirim istenir. <br> - Puanlama kriterleri prompt'ta net tanımlanır (anahtar kelimelerin kullanımı, akıl yürütme, örnek cevaplar). [cite_start]<br> - Al'dan dönen sonuç JSON olarak parse edilip Answer tablosuna kaydedilir. [cite: 33] |
| **4.3** | [cite_start]Konu etiketleme: Soru üretiminde Al'dan gelen topic alanı doğrudan `Question.topic`'e yazılır. [cite: 33] |
| **4.4** | Analitik raporlar: <br> - Toplam puan, konu bazında doğru/yanlış sayıları, gelişim grafikleri (basit bar chart veya radar chart). Chart.js veya Recharts kullanılacak. [cite_start]<br> - "Yanlış yapılan konular" listesi ile öneri metni (örneğin "Türev konusuna tekrar çalışmanız önerilir"). [cite: 33] |

### [cite_start]İP5: Test, Dokümantasyon ve Deployment [cite: 34]

| Görev No | Açıklama |
| :--- | :--- |
| **5.1** | [cite_start]Birim testler: Backend'de API endpoint'leri için pytest; frontend'de bileşen testleri (Jest + React Testing Library). [cite: 35] |
| **5.2** | [cite_start]Entegrasyon testleri: OCR → soru üretimi → puanlama akışının uçtan uca testi. [cite: 35] |
| **5.3** | Al çıktı doğrulama: Al'dan gelen JSON'ların şema validasyonu (Pydantic modelleri ile). [cite_start]Geçersiz çıktılarda yeniden deneme veya fallback mekanizması. [cite: 35] |
| **5.4** | [cite_start]API dokümantasyonu: FastAPI'nin otomatik Swagger dokümantasyonu kullanılacak. [cite: 35] |
| **5.5** | [cite_start]Kullanıcı kılavuzu: Uygulama içi yardım sayfası ve basit bir PDF kılavuz hazırlanması. [cite: 35] |
| **5.6** | Deployment: <br> - Backend: Railway veya Google Cloud Run'da containerize edilmiş olarak çalıştırılması. <br> - Frontend: Vercel veya Netlify üzerinde statik hosting. [cite_start]<br> - Ortam değişkenleri ve API anahtarları güvenli şekilde yönetilecek. [cite: 35] |

---

## [cite_start]Teknik Uygulama Notları [cite: 36]

### [cite_start]Frontend Teknolojileri [cite: 37]
* [cite_start]React + Vite (hızlı geliştirme ortamı) [cite: 38]
* [cite_start]TailwindCSS veya Material-UI (responsive tasarım) [cite: 39]
* [cite_start]Axios (API istekleri) [cite: 40]
* [cite_start]React Router (sayfa yönlendirmeleri) [cite: 41]
* [cite_start]React Hook Form + Zod (form yönetimi ve validasyon) / React Query (server state yönetimi) [cite: 42]
* [cite_start]Recharts / Chart.js (grafikler) [cite: 43]
* [cite_start]React-Dropzone (sürükle-bırak dosya yükleme) [cite: 44]
* [cite_start]Tesseract.js (client-side OCR opsiyonu) [cite: 45]

### [cite_start]Backend Teknolojileri [cite: 46]
* [cite_start]FastAPI (Python) [cite: 47]
* [cite_start]PostgreSQL + SQLAlchemy (ORM) [cite: 48]
* [cite_start]Redis (önbellekleme ve Celery broker) [cite: 49]
* [cite_start]Celery (asenkron görev yönetimi) [cite: 50]
* [cite_start]Google Cloud Vision API / Tesseract (OCR) [cite: 51]
* [cite_start]Gemini 1.5 Flash API (Al soru üretimi ve puanlama) [cite: 52]

---

## [cite_start]Token Tasarrufu Stratejileri [cite: 53]
* [cite_start]Test değerlendirmesinde Al kullanılmaz. [cite: 54]
* [cite_start]Uzun notlar özetlenerek token girişi azaltılır. [cite: 55]
* [cite_start]Önbellekleme ile tekrar eden üretimler engellenir. [cite: 56]
* [cite_start]Batch üretim (tek istekte hem test hem açık uçlu) ile çağrı sayısı düşürülür. [cite: 57]

---

## [cite_start]Hata Yönetimi [cite: 58]
* [cite_start]API limit aşımlarında exponential backoff ile yeniden deneme. [cite: 59]
* [cite_start]Al'dan dönen yanıtın geçersiz olması durumunda fallback olarak kullanıcıya "Sınav oluşturulamadı, lütfen tekrar deneyin" mesajı. [cite: 60]
* [cite_start]Tüm hatalar loglanır (Cloud Logging veya dosya). [cite: 61]

---

## [cite_start]Güvenlik ve Gizlilik [cite: 62]
* [cite_start]Kullanıcı notları şifrelenerek veritabanında saklanır. [cite: 63]
* [cite_start]Al servisine gönderilen veriler anonimleştirilir (kullanıcı adı vb. gönderilmez). [cite: 64]
* [cite_start]Google Cloud ile yapılan tüm iletişim HTTPS üzerinden yapılır. [cite: 65]
* [cite_start]JWT token'lar HTTP-only cookie ile saklanır (XSS koruması). [cite: 66]

---

## [cite_start]Performans ve UX [cite: 67]
* [cite_start]Görseller backend'e gönderilmeden önce boyutlandırılır (max 1024x1024). [cite: 68]
* [cite_start]Asenkron işlemler sayesinde kullanıcı arayüzü bloke edilmez. [cite: 69]
* [cite_start]Lazy loading ile sayfa yüklemeleri optimize edilir. [cite: 70]
* [cite_start]PWA desteği ile mobil cihazlarda ana ekrana eklenebilir web uygulaması deneyimi. [cite: 71]

---

## [cite_start]Zaman Çizelgesi (Öneri) [cite: 72]

| Hafta | Yapılacaklar |
| :--- | :--- |
| **1-2** | [cite_start]İP1 (Altyapı, veritabanı, auth) [cite: 73] |
| **3-4** | [cite_start]İP2 (Görüntü işleme, OCR) [cite: 73] |
| **5-6** | [cite_start]İP3 (Soru üretimi, token optimizasyonu, asenkron yapı) [cite: 73] |
| **7** | [cite_start]İP4 (Puanlama, grafikler) [cite: 73] |
| **8** | [cite_start]İP5 (Test, dokümantasyon, deployment) [cite: 73] |