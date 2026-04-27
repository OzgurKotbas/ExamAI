# ExamAI Nihai Proje Raporu ve Teknik Dokümantasyon

Bu döküman, ExamAI platformunun tüm teknik bileşenlerini, dosya yapılarını, API eşleşmelerini ve kurulum talimatlarını içeren kapsamlı nihai rapordur.

---

## 1. Proje Genel Bakış

**ExamAI**, öğrencilerin ders notlarından (PDF, Görsel, Metin, Word) yapay zeka yardımıyla (Gemini 1.5 Flash) kişiselleştirilmiş sınavlar üreten multimodal bir web uygulamasıdır. Uygulama, test sorularını backend üzerinde anlık olarak, açık uçlu soruları ise yapay zeka üzerinden hibrit bir yöntemle değerlendirir.

---

## 2. Dosya Yapısı ve Görevleri

### 📂 `backendWindsurf2/` (Sunucu Tarafı)
- **`main.py`**: Uygulamanın giriş noktası. FastAPI uygulamasını başlatır, router'ları bağlar ve CORS ayarlarını yönetir.
- **`config.py`**: Çevre değişkenlerini (`.env`) ve genel uygulama ayarlarını yöneten Pydantic tabanlı yapılandırma.
- **`database.py`**: SQLAlchemy ve Asyncpg kullanarak asenkron veritabanı bağlantılarını ve session yönetimini sağlar.
- **`celery_app.py`**: Arka plan görevleri (Quiz üretimi, OCR işleme) için Celery konfigürasyonu.
- **📂 `models/`**: Veritabanı tabloları (User, Note, Quiz, Question, Answer, GradingSession).
- **📂 `routers/`**:
    - `auth.py`: Kayıt, giriş, Google OAuth ve şifre işlemleri.
    - `notes.py`: Dosya yükleme ve metin çıkarma tetiklemeleri.
    - `quiz.py`: Sınav oluşturma, durum sorgulama ve cevap gönderme işlemleri.
- **📂 `services/`**:
    - `ai_service.py`: Gemini API ile soru üretimi ve açık uçlu soru puanlama.
    - `auth_service.py`: JWT üretimi, şifre hashleme ve Google login mantığı.
    - `ocr_service.py`: Tesseract ve OpenCV ile görselden/PDF'den metin çıkarma.
    - `extraction_service.py`: PDF, Word ve Text dosyalarından metin okuma.
- **📂 `utils/`**: Şifreleme (AES-256) ve Logger yardımcıları.

### 📂 `examai-frontend/` (İstemci Tarafı)
- **`src/App.jsx`**: Uygulamanın ana rotalarını (Routing) ve Provider'ları (Auth, Theme, Language) yönetir.
- **📂 `src/api/index.js`**: Backend endpoint'leri ile haberleşen `quizzesApi`, `authApi`, `notesApi` servislerini içerir.
- **📂 `src/pages/`**:
    - `Login.jsx` & `Register.jsx`: Kullanıcı giriş/kayıt ekranları.
    - `Dashboard.jsx`: Not yükleme ve sınav listeleme ekranı.
    - `Quiz.jsx`: Sınav çözme ve sonuç görüntüleme ekranı.
    - `AuthCallback.jsx`: Google login sonrası yönlendirme mantığı.
    - `ForgotPassword.jsx`: Şifre sıfırlama akışı.
- **📂 `src/context/`**: Global state yönetimi (Kimlik doğrulama, Dil, Tema).

---

## 3. Endpoint - Arayüz Eşleşme Tablosu

| Backend Endpoint (API/v1) | Frontend Fonksiyonu (`api/index.js`) | Kullanıldığı Sayfa | Görevi |
| :--- | :--- | :--- | :--- |
| `POST /auth/register` | `authApi.register` | `Register.jsx` | Yeni kullanıcı kaydı. |
| `POST /auth/login` | `authApi.login` | `Login.jsx` | E-posta/Şifre ile giriş. |
| `GET /auth/google` | `authApi.googleLogin` | `Login.jsx` | Google OAuth yönlendirmesi. |
| `GET /auth/me` | `authApi.me` | `AuthContext.jsx` | Oturum açan kullanıcıyı doğrular. |
| `POST /notes` | `notesApi.upload` | `Dashboard.jsx` | Dosya (PDF/Görsel) yükleme. |
| `GET /notes` | `notesApi.list` | `Dashboard.jsx` | Kullanıcının notlarını listeleme. |
| `POST /quizzes` | `quizzesApi.create` | `Dashboard.jsx` | Yeni sınav oluşturma isteği. |
| `GET /quizzes/{id}/status` | `quizzesApi.getStatus` | `Quiz.jsx` | Sınav üretim durumunu takip eder. |
| `GET /quizzes/{id}/questions` | `quizzesApi.getQuestions`| `Quiz.jsx` | Sınav sorularını getirir. |
| `POST /quizzes/{id}/submit` | `quizzesApi.submit` | `Quiz.jsx` | Cevapları değerlendirme için gönderir. |
| `GET /quizzes/{id}/grading/{gid}`| `quizzesApi.getResults` | `Quiz.jsx` | Puanlanmış sonuçları getirir. |
| `DELETE /quizzes/{id}` | `quizzesApi.delete` | `Dashboard.jsx` | Sınavı kalıcı olarak siler. |

---

## 4. Boşta (Orphaned) Endpoint Analizi

Analizler sonucunda aşağıdaki endpoint'lerin backend'de tanımlı olduğu ancak frontend arayüzünde (henüz) karşılıklarının bulunmadığı tespit edilmiştir:

1.  **`PUT /api/v1/auth/profile`**: Kullanıcı adı ve e-posta güncelleme. (Frontend'de Profil Düzenleme ekranı henüz yok).
2.  **`POST /api/v1/auth/change-password`**: Mevcut şifreyi değiştirme. (Kullanıcı panelinde ayarlar sekmesi henüz yok).
3.  **`/api/v1/health`**: Sunucu sağlık kontrolü. (Sadece sistem yönetimi/izleme için kullanılır, UI gerektirmez).

---

## 5. Uygulamayı Başka Bilgisayarda Çalıştırma (Portability)

Uygulamayı sıfır bir makinede çalıştırmak için aşağıdaki adımları izleyin:

### Gereksinimler (Prerequisites)
- **Python 3.10+** (Backend için)
- **Node.js 18+** (Frontend için)
- **Redis Server** (Windows'ta `memurai` veya Docker ile çalıştırılabilir)
- **PostgreSQL** (Veritabanı olarak)
- **Tesseract OCR**: [Buradan indirin](https://github.com/UB-Mannheim/tesseract/wiki) ve sistem PATH'ine ekleyin.

### Kurulum Adımları
1.  **Backend Kurulumu**:
    ```bash
    cd backendWindsurf2
    python -m venv .venv
    .\.venv\Scripts\activate
    pip install -r requirements.txt
    ```
2.  **Veritabanı ve Çevre Değişkenleri**:
    - `.env` dosyasını oluşturun ve veritabanı bilgilerini, Gemini API anahtarını ve Google OAuth bilgilerini girin.
3.  **Frontend Kurulumu**:
    ```bash
    cd examai-frontend
    npm install
    ```
4.  **Uygulamayı Başlatma**:
    - Kök dizindeki `start_all.bat` dosyasını çalıştırarak veritabanı, redis, celery, backend ve frontend'i aynı anda başlatabilirsiniz.

---

## 6. Veri Saklama ve Güvenlik

- **Hesap Bilgileri**: `User` tablosunda PostgreSQL üzerinde saklanır. Şifreler `Bcrypt` algoritması ile tek yönlü hashlenir.
- **Sınav Bilgileri**: `Quiz`, `Question` ve `Answer` tablolarında tutulur.
- **Not İçerikleri**: Kullanıcı gizliliği için **AES-256-GCM** algoritması ile şifrelenmiş (Encrypted) olarak saklanır. Sadece sahibi erişebilir.
- **Oturum Yönetimi**: `JWT (JSON Web Token)` kullanılır.

---

## 7. Proje Planı ve Gereksinim Analizi (ExamAI.md Audit)

`ExamAI.md` ve Proje Planı'nda istenen maddelerin durum raporu:

| İstenen Özellik | Durum | Uygulama Yöntemi |
| :--- | :--- | :--- |
| **Multimodal Giriş** | ✅ Tamam | PDF, Image, Word ve Text desteği eklendi. |
| **Google OAuth** | ✅ Tamam | Mevcut kullanıcıyı Dashboard'a, yeniyi Kayıt'a yönlendirme eklendi. |
| **Hibrit Puanlama** | ✅ Tamam | Test soruları backend'de anlık, açık uçlu sorular Gemini AI ile puanlanıyor. |
| **Anlık Puanlama (Instant)** | ✅ Tamam | Test sınavlarında bekleme süresini kaldıran özel `submit` mantığı eklendi. |
| **Token Optimizasyonu** | ✅ Tamam | Test değerlendirmesinde AI kullanılmayarak token tasarrufu sağlandı. |
| **Asenkron Yapı** | ✅ Tamam | Celery + Redis + Solo Worker (Windows) mimarisi kuruldu. |
| **AES-256 Şifreleme** | ✅ Tamam | `cryptography` kütüphanesi ile not güvenliği sağlandı. |
| **Analitik Dashboard** | ✅ Tamam | Recharts ve Chart.js entegrasyonu ile başarı yüzdeleri gösteriliyor. |

---
*Bu nihai rapor Antigravity tarafından 06.04.2026 tarihinde projenin tamamlanmış hali üzerinden oluşturulmuştur.*
