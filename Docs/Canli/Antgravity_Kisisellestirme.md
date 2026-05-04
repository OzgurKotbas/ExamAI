# Kişiselleştirilmiş Gemini API Anahtarı Özelliği

Bu döküman, ExamAI platformunda kullanıcıların kendi Gemini API anahtarını kullanabilmelerini sağlayan "Kişiselleştirme" özelliğinin detaylarını içerir.

## Yapılan Değişiklikler

### 1. Backend (FastAPI)
- **Model:** `backendWindsurf2/models/user.py` dosyasına `gemini_api_key` alanı eklendi.
- **Şema:** `backendWindsurf2/schemas/user.py` dosyasındaki `UserRead` şeması bu yeni alanı içerecek şekilde güncellendi.
- **Servis:** `backendWindsurf2/services/auth_service.py` içindeki `update_user_profile` fonksiyonu, API anahtarını kaydedecek şekilde güncellendi.
- **Router:** `backendWindsurf2/routers/auth.py` içindeki `/profile` endpoint'i yeni parametreyi kabul edecek hale getirildi.
- **AI Servisi:** `backendWindsurf2/services/ai_service.py` içindeki tüm üretim ve notlandırma fonksiyonları, kullanıcı anahtarı varsa onu öncelikli kullanacak şekilde refaktör edildi.
- **Celery:** `backendWindsurf2/services/celery_tasks.py` arka plan görevleri artık ilgili kullanıcının API anahtarını çekip AI servisine iletiyor.

### 2. Frontend (React)
- **API Katmanı:** `examai-frontend/src/api/index.js` içindeki `updateProfile` fonksiyonu yeni alanı destekleyecek şekilde güncellendi.
- **UI:** `examai-frontend/src/components/ProfileMenu.jsx` içindeki "Hesap Bilgileri" modalına **Gemini API Anahtarı** giriş alanı eklendi.
- **Dil:** `examai-frontend/src/context/LanguageContext.jsx` dosyasına Türkçe ve İngilizce yeni çeviriler eklendi.

## Nasıl Kullanılır?

1.  Uygulamaya giriş yapın.
2.  Sağ üstteki profil menüsünden **Hesap Bilgileri** (Account Info) seçeneğine tıklayın.
3.  **Düzenle** (Edit) butonuna basın.
4.  **Gemini API Anahtarı** alanına kendi anahtarınızı (`AIzaSy...` ile başlayan) yapıştırın.
5.  **Kaydet** (Save) butonuna basın.

Artık oluşturacağınız tüm sınavlar ve alacağınız tüm değerlendirmeler **sizin kendi API anahtarınız** üzerinden işlem görecektir. Eğer bu alanı boş bırakırsanız, sistem otomatik olarak geliştiricinin varsayılan anahtarını kullanmaya devam eder.

## Teknik Not
Kullanıcı anahtarı girildiğinde, sistem önce Hugging Face modellerini denemez, doğrudan kullanıcının Gemini anahtarı ile işlem yapmaya çalışır. Bu sayede "Tek Sohbet" (Single Context) mantığına daha yakın bir deneyim hedeflenmiştir.
