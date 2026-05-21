# Hata Mesajları Çoklu Dil Desteği (i18n) - Mayıs 2026

Bu güncelleme ile ExamAI backend servisleri ve frontend entegrasyonu, seçili dile göre hata mesajı döndürecek şekilde güncellenmiştir.

## Yapılan Değişiklikler

### 1. Backend i18n Altyapısı
- `backendWindsurf2/utils/i18n.py` dosyası oluşturuldu.
- Bu dosya içinde `MESSAGES` sözlüğü ile tüm hata ve başarı mesajları Türkçe ve İngilizce olarak tanımlandı.
- `translate(key, lang)` yardımcı fonksiyonu ile mesajların dinamik olarak getirilmesi sağlandı.

### 2. Router ve Servis Güncellemeleri
- **X-Language Header:** Tüm API endpoint'leri artık Header üzerinden `X-Language` bilgisini kabul ediyor (varsayılan: `tr`).
- **Auth, Quiz ve Notes Router'ları:** Gelen dil bilgisi yakalanarak servis katmanlarına iletiliyor.
- **Servis Katmanları:** `auth_service.py` ve `ai_service.py` içindeki tüm `ValueError` ve `HTTPException` mesajları `translate` fonksiyonu kullanacak şekilde güncellendi.

### 3. Frontend Entegrasyonu
- `examai-frontend/src/api/index.js` dosyasındaki `axios` interceptor'ı güncellendi.
- Artık her istekte `localStorage` üzerindeki `language` bilgisi otomatik olarak `X-Language` header'ı ile backend'e gönderiliyor.
- Login sayfasındaki 401 hatası yönlendirme döngüsü düzeltildi; böylece yanlış şifre girildiğinde hata mesajı ekranda görünüyor.

## Kullanılan Dosyalar
- `backendWindsurf2/utils/i18n.py` [YENİ]
- `backendWindsurf2/services/auth_service.py` [GÜNCELLENDİ]
- `backendWindsurf2/services/ai_service.py` [GÜNCELLENDİ]
- `backendWindsurf2/routers/auth.py` [GÜNCELLENDİ]
- `backendWindsurf2/routers/quiz.py` [GÜNCELLENDİ]
- `backendWindsurf2/routers/notes.py` [GÜNCELLENDİ]
- `examai-frontend/src/api/index.js` [GÜNCELLENDİ]

## Test Senaryosu
1. Uygulama dilini İngilizce yapın.
2. Yanlış şifre ile giriş yapmayı deneyin -> "Invalid email or password." uyarısını görmelisiniz.
3. Uygulama dilini Türkçe yapın.
4. Yanlış şifre ile giriş yapmayı deneyin -> "E-posta adresi veya şifre hatalı." uyarısını görmelisiniz.
