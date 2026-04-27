# ExamAI Frontend Raporu

## Proje Özeti

Bu rapor, ExamAI projesinin frontend geliştirme sürecinde yapılan çalışmaları ve uygulanan özellikleri dokümante etmektedir.

**Proje:** ExamAI - Yapay Zeka Destekli Sınav Platformu  
**Tarih:** 5 Nisan 2026  
**Frontend Teknoloji Stack:** React + Vite, TailwindCSS, React Router, Axios

---

## Geliştirilen Özellikler

### 1. Kimlik Doğrulama Sistemi (Authentication)

#### 1.1 Login Sayfası (`src/pages/Login.jsx`)
- **Özellikler:**
  - E-posta ve şifre ile giriş
  - Form validasyonu (Zod + React Hook Form)
  - Şifre görünürlüğü toggle (gizle/göster)
  - Google OAuth entegrasyonu
  - Hata mesajları ve toast bildirimleri
  - Responsive tasarım

#### 1.2 Register Sayfası (`src/pages/Register.jsx`)
- **Özellikler:**
  - Ad soyad, e-posta, şifre kayıt formu
  - Şifre doğrulama (şifre tekrarı)
  - Form validasyonu
  - Başarılı kayıt sonrası otomatik giriş
  - Google ile kayıt seçeneği

#### 1.3 Forgot Password Sayfası (`src/pages/ForgotPassword.jsx`)
- **Özellikler:**
  - İki adımlı şifre sıfırlama akışı:
    1. E-posta adresine sıfırlama kodu gönderme
    2. Kod doğrulama ve yeni şifre belirleme
  - 6 haneli doğrulama kodu
  - Şifre eşleşme kontrolü
  - Redis üzerinde kod saklama (10 dakika geçerlilik)

---

### 2. Dashboard ve Ana Menü

#### 2.1 Dashboard Sayfası (`src/pages/Dashboard.jsx`)
- **Özellikler:**
  - Kullanıcı karşılama ekranı
  - İstatistik kartları:
    - Yüklenen kaynak sayısı
    - Oluşturulan sınav sayısı
    - Tamamlanan sınav sayısı
  - Tab bazlı navigasyon (Yeni Sınav / Geçmiş Sınavlar)
  - Navbar ile kullanıcı bilgisi ve çıkış

#### 2.2 Dosya Yükleme Bileşeni (`src/components/FileUpload.jsx`)
- **Özellikler:**
  - Sürükle-bırak desteği (react-dropzone)
  - Desteklenen formatlar: PDF, JPG, PNG, TXT
  - Maksimum 20MB dosya boyutu
  - Dosya önizleme ve seçim iptali
  - Yükleme durumu göstergesi

#### 2.3 Sınav Oluşturma Modalı
- **Özellikler:**
  - Kaynak seçimi
  - Soru sayısı ayarı (5-50 arası slider)
  - Test / Açık uçlu oranı ayarı (%0-100)
  - Zorluk seviyesi seçimi (Kolay/Orta/Zor)
  - Yapay zeka entegrasyonu ile sınav hazırlama

---

### 3. API Entegrasyonu

#### 3.1 API Yapılandırması (`src/api/index.js`)
- **Özellikler:**
  - Axios instance yapılandırması
  - JWT token interceptor (request/response)
  - 401 hatası handling (otomatik logout)
  - Endpoint grupları:
    - Auth API (login, register, forgot/reset password, Google OAuth)
    - Notes API (upload, list)
    - Quizzes API (create, list, get status, submit)

#### 3.2 Auth Context (`src/context/AuthContext.jsx`)
- **Özellikler:**
  - Global kimlik durumu yönetimi
  - Token saklama (localStorage)
  - Kullanıcı otomatik yükleme (token varsa)
  - Login/logout fonksiyonları

#### 3.3 Protected Route (`src/components/ProtectedRoute.jsx`)
- **Özellikler:**
  - Kimlik doğrulama kontrolü
  - Yükleme durumu göstergesi
  - Yetkisiz erişim yönlendirmesi

---

### 4. Backend Entegrasyonu

#### 4.1 Şifre Sıfırlama Endpoint'leri (Backend)
- **Dosyalar:**
  - `services/email_service.py` - E-posta gönderme servisi
  - `services/auth_service.py` - Şifre sıfırlama fonksiyonları
  - `routers/auth.py` - API endpoint'leri

- **Özellikler:**
  - `/auth/forgot-password` - Sıfırlama kodu gönderme
  - `/auth/reset-password` - Kod doğrulama ve şifre sıfırlama
  - Redis tabanlı kod saklama (10 dk geçerlilik)
  - HTML e-posta şablonları
  - Güvenlik: Kullanıcı varlığı dışarıya açılmıyor

#### 4.2 Config Güncellemeleri
- **Yeni ayarlar:**
  - SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
  - SMTP_FROM, FRONTEND_URL
  - PASSWORD_RESET_TOKEN_EXPIRE_HOURS, RESET_CODE_EXPIRE_MINUTES

#### 4.3 Schema Güncellemeleri
- **Yeni schema'lar:**
  - PasswordResetRequest
  - PasswordResetVerify
  - PasswordResetResponse
  - MessageResponse

---

### 5. UI/UX Tasarımı

#### 5.1 Tasarım Sistemi
- **Renk Paleti:**
  - Primary: Indigo (#6366f1) → Purple (#9333ea)
  - Success: Green (#10B981)
  - Error: Red (#EF4444)
  - Background: Gray gradient

#### 5.2 Bileşenler
- **LoadingSpinner:** Farklı boyutlarda yükleme göstergesi
- **Toast Bildirimleri:** react-hot-toast ile başarı/hata mesajları
- **Responsive Grid:** TailwindCSS grid sistemi

---

## Dosya Yapısı

```
examai-frontend/src/
├── api/
│   └── index.js              # API endpoint'leri ve axios yapılandırması
├── components/
│   ├── FileUpload.jsx        # Dosya yükleme bileşeni
│   ├── LoadingSpinner.jsx    # Yükleme göstergesi
│   └── ProtectedRoute.jsx    # Korumalı rota wrapper'ı
├── context/
│   └── AuthContext.jsx       # Kimlik doğrulama context'i
├── pages/
│   ├── Dashboard.jsx         # Ana dashboard sayfası
│   ├── ForgotPassword.jsx    # Şifre sıfırlama sayfası
│   ├── Login.jsx             # Giriş sayfası
│   └── Register.jsx          # Kayıt sayfası
├── App.jsx                   # Ana uygulama ve routing
└── main.jsx                  # Uygulama giriş noktası
```

---

## Backend Dosya Değişiklikleri

```
backendWindsurf2/
├── config.py                 # E-posta ve şifre sıfırlama ayarları
├── schemas/user.py           # Şifre sıfırlama schema'ları
├── services/
│   ├── auth_service.py       # Şifre sıfırlama fonksiyonları
│   └── email_service.py      # E-posta gönderme servisi (YENİ)
├── routers/auth.py           # Şifre sıfırlama endpoint'leri
└── .env.example              # Yeni environment değişkenleri
```

---

## API Endpoint'leri

### Kimlik Doğrulama
| Endpoint | Metod | Açıklama |
|----------|-------|----------|
| `/api/v1/auth/register` | POST | Yeni kullanıcı kaydı |
| `/api/v1/auth/login` | POST | E-posta/şifre ile giriş |
| `/api/v1/auth/google` | GET | Google OAuth yönlendirmesi |
| `/api/v1/auth/google/callback` | GET | Google OAuth callback |
| `/api/v1/auth/me` | GET | Mevcut kullanıcı bilgisi |
| `/api/v1/auth/forgot-password` | POST | Şifre sıfırlama kodu gönder |
| `/api/v1/auth/reset-password` | POST | Şifre sıfırlama kodu doğrula |

### Notlar
| Endpoint | Metod | Açıklama |
|----------|-------|----------|
| `/api/v1/notes` | GET | Kullanıcının notlarını listele |
| `/api/v1/notes` | POST | Yeni not/dosya yükle |

### Sınavlar
| Endpoint | Metod | Açıklama |
|----------|-------|----------|
| `/api/v1/quizzes` | GET | Sınav geçmişini listele |
| `/api/v1/quizzes` | POST | Yeni sınav oluştur |
| `/api/v1/quizzes/{id}/status` | GET | Sınav durumunu kontrol et |
| `/api/v1/quizzes/{id}/submit` | POST | Sınav cevaplarını gönder |

---

## Kurulum Talimatları

### 1. Frontend Kurulumu
```bash
cd examai-frontend
npm install
npm run dev
```

### 2. Backend Kurulumu
```bash
cd backendWindsurf2
# Python sanal ortamı aktive et
pip install -r requirements.txt
# .env dosyasını yapılandır
uvicorn main:app --reload
```

### 3. Environment Değişkenleri
Frontend `.env`:
```
VITE_API_URL=http://localhost:8000
```

Backend `.env`:
```
# SMTP Ayarları (Gmail örneği)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=ExamAI <noreply@examai.com>
FRONTEND_URL=http://localhost:5173
```

---

## Güvenlik Özellikleri

1. **JWT Token Yönetimi**
   - HTTP-only cookie tabanlı (XSS koruması)
   - Otomatik token yenileme
   - 401 hatası durumunda otomatik logout

2. **Şifre Sıfırlama**
   - 6 haneli rastgele kod
   - 10 dakika geçerlilik süresi (Redis)
   - Tek kullanımlık kod
   - E-posta varlığı gizlenmesi

3. **Form Validasyonu**
   - Zod schema validasyonu
   - E-posta format kontrolü
   - Şifre uzunluğu ve eşleşme kontrolü

4. **Dosya Yükleme**
   - Dosya tipi kontrolü (PDF, JPG, PNG, TXT)
   - Dosya boyutu limiti (20MB)
   - Dosya uzantısı validasyonu

---

## Kullanıcı Akışı

1. **Kayıt → Giriş → Dashboard**
   - Kullanıcı kaydolur veya giriş yapar
   - JWT token alır ve localStorage'da saklanır
   - Dashboard'a yönlendirilir

2. **Kaynak Yükleme**
   - Dosya sürükle-bırak veya seçim
   - API'ye yüklenir ve işlenir
   - Not listesinde görünür

3. **Sınav Oluşturma**
   - Kaynak seçimi
   - Soru sayısı, test/açık uçlu oranı, zorluk seviyesi
   - AI API'ye gönderilir (asenkron)
   - Hazır olduğunda kullanıcıya bildirim

4. **Şifre Sıfırlama**
   - E-posta girilir
   - 6 haneli kod e-posta ile gönderilir
   - Kod doğrulanır ve yeni şifre belirlenir

---

## Gelecek Geliştirmeler

- [ ] Quiz detay sayfası (soru çözüm)
- [ ] Analitik raporlar ve grafikler
- [ ] Gerçek zamanlı bildirimler (WebSocket)
- [ ] Mobil uygulama (PWA)
- [ ] Çoklu dil desteği (i18n)

---

**Not:** Bu frontend, ExamAI.md ve ExamAI Proje Planı.pdf dokümanlarındaki teknik gereksinimlere göre geliştirilmiştir.
