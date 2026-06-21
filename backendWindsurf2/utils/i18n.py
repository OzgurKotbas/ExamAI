from typing import Dict

# Hata mesajları sözlüğü
MESSAGES: Dict[str, Dict[str, str]] = {
    # Auth
    "EMAIL_EXISTS": {
        "tr": "Bu e-posta adresiyle kayıtlı bir kullanıcı zaten mevcut.",
        "en": "User with this email already exists."
    },
    "INVALID_CREDENTIALS": {
        "tr": "E-posta adresi veya şifre hatalı.",
        "en": "Invalid email or password."
    },
    "ACCOUNT_INACTIVE": {
        "tr": "Kullanıcı hesabı aktif değil. Lütfen e-postanızı kontrol edin.",
        "en": "User account is inactive. Please check your email."
    },
    "AUTH_FAILED": {
        "tr": "Kimlik doğrulama başarısız oldu.",
        "en": "Authentication failed."
    },
    "MISSING_AUTH_HEADER": {
        "tr": "Oturum bilgisi eksik. Lütfen tekrar giriş yapın.",
        "en": "Missing Authorization header. Please login again."
    },
    "INVALID_TOKEN": {
        "tr": "Oturum süresi dolmuş veya geçersiz. Lütfen tekrar giriş yapın.",
        "en": "Invalid or expired token. Please login again."
    },
    "INTERNAL_SERVER_ERROR": {
        "tr": "Sunucu tarafında bir hata oluştu.",
        "en": "Internal server error."
    },
    "REGISTRATION_FAILED": {
        "tr": "Kayıt işlemi sırasında bir hata oluştu.",
        "en": "Failed to register user."
    },
    "LOGIN_FAILED": {
        "tr": "Giriş işlemi sırasında bir hata oluştu.",
        "en": "Failed to login."
    },
    "PROFILE_UPDATE_FAILED": {
        "tr": "Profil güncellenemedi.",
        "en": "Failed to update profile."
    },
    "EMAIL_IN_USE": {
        "tr": "Bu e-posta adresi başka bir kullanıcı tarafından kullanılıyor.",
        "en": "Email address is already in use."
    },
    "CURRENT_PASSWORD_INCORRECT": {
        "tr": "Mevcut şifreniz hatalı.",
        "en": "Current password is incorrect."
    },
    "PASSWORD_CHANGE_FAILED": {
        "tr": "Şifre değiştirilemedi.",
        "en": "Failed to change password."
    },
    "PASSWORD_CHANGE_SUCCESS": {
        "tr": "Şifreniz başarıyla değiştirildi.",
        "en": "Password changed successfully."
    },
    "RESET_CODE_SENT": {
        "tr": "Sıfırlama kodu e-posta adresinize gönderildi.",
        "en": "Reset code sent to your email."
    },
    "RESET_CODE_FALLBACK": {
        "tr": "Eğer bu e-posta adresi sistemde kayıtlıysa, bir sıfırlama kodu gönderilmiştir.",
        "en": "If the email exists, a reset code has been sent."
    },
    "INVALID_RESET_CODE": {
        "tr": "Geçersiz veya süresi dolmuş sıfırlama kodu.",
        "en": "Invalid or expired reset code."
    },
    "USER_NOT_FOUND": {
        "tr": "Kullanıcı bulunamadı.",
        "en": "User not found."
    },
    "PASSWORD_RESET_SUCCESS": {
        "tr": "Şifreniz başarıyla sıfırlandı.",
        "en": "Password reset successfully."
    },

    # AI & Quiz
    "AI_ALL_FAILED": {
        "tr": "Tüm yapay zeka servisleri başarısız oldu. Lütfen tekrar deneyin.",
        "en": "All AI providers failed. Please try again."
    },
    "AI_PARSE_ERROR": {
        "tr": "Yapay zeka yanıtı işlenemedi. Lütfen tekrar deneyin.",
        "en": "Could not parse JSON response from AI."
    },
    "GEMINI_KEY_MISSING": {
        "tr": "Gemini API anahtarı yapılandırılmamış. Lütfen profilinizden API anahtarınızı ekleyin.",
        "en": "Gemini API key not configured. Please add it in your profile."
    },
    "QUIZ_NOT_FOUND": {
        "tr": "Sınav bulunamadı.",
        "en": "Quiz found."
    },
    "QUIZ_NOT_READY": {
        "tr": "Sınav henüz hazır değil.",
        "en": "Quiz is not ready yet."
    },
    "NOTE_NOT_FOUND": {
        "tr": "Not bulunamadı.",
        "en": "Note not found."
    },
    "NOTE_NO_CONTENT": {
        "tr": "İçeriği olmayan bir nottan sınav oluşturulamaz.",
        "en": "Cannot create quiz from note without content."
    },
    "NOTE_TOO_SHORT": {
        "tr": "Not içeriği anlamlı sorular oluşturmak için çok kısa.",
        "en": "Note content is too short to generate questions."
    },
    "QUIZ_GEN_FAILED": {
        "tr": "Sınav oluşturulurken bir hata oluştu.",
        "en": "Failed to create quiz."
    },
    "GRADING_NOT_FOUND": {
        "tr": "Değerlendirme oturumu bulunamadı.",
        "en": "Grading session not found."
    },
    "GRADING_NOT_READY": {
        "tr": "Değerlendirme henüz tamamlanmadı.",
        "en": "Grading is not completed yet."
    },
    "NO_ANSWERS_FOUND": {
        "tr": "Bu sınav için cevap bulunamadı.",
        "en": "No answers found for this quiz."
    },

    # Notes
    "UPLOAD_SUCCESS": {
        "tr": "Notlar başarıyla yüklendi.",
        "en": "Notes uploaded successfully."
    },
    "UNSUPPORTED_FORMAT": {
        "tr": "Desteklenmeyen dosya formatı.",
        "en": "Unsupported file format."
    },
    "MAX_FILES_EXCEEDED": {
        "tr": "En fazla 10 dosya yükleyebilirsiniz.",
        "en": "Maximum 10 files allowed."
    },

    # Gemini API Key Validation
    "GEMINI_KEY_VALID": {
        "tr": "✅ API anahtarı ve model başarıyla doğrulandı.",
        "en": "✅ API key and model validated successfully."
    },
    "GEMINI_KEY_INVALID": {
        "tr": "❌ API anahtarı geçersiz veya yetkisiz. Lütfen Google AI Studio'dan yeni bir anahtar alın.",
        "en": "❌ Invalid or unauthorized API key. Please get a new key from Google AI Studio."
    },
    "GEMINI_MODEL_NOT_FOUND": {
        "tr": "⚠️ Seçilen model bu API anahtarı için erişilebilir değil. Farklı bir model deneyin.",
        "en": "⚠️ The selected model is not accessible with this API key. Try a different model."
    },
    "GEMINI_QUOTA_EXCEEDED": {
        "tr": "⚠️ API kotanız dolmuş. Bir süre bekleyip tekrar deneyin veya planınızı yükseltin.",
        "en": "⚠️ API quota exceeded. Wait a moment and try again, or upgrade your plan."
    },
    "GEMINI_CONNECTION_ERROR": {
        "tr": "🔌 Google API'ye bağlanılamadı. İnternet bağlantınızı kontrol edin.",
        "en": "🔌 Could not connect to Google API. Check your internet connection."
    },
    "GEMINI_PROJECT_ID_INVALID": {
        "tr": "Google Cloud proje kimliği geçersiz. Hizmet hesabı veya kimlik bilgisi yapılandırmanızı kontrol edin.",
        "en": "Invalid Google Cloud project ID. Please check your service account or credential configuration."
    },
    "GEMINI_VALIDATION_FAILED": {
        "tr": "Doğrulama sırasında beklenmeyen bir hata oluştu.",
        "en": "An unexpected error occurred during validation."
    },
    "GEMINI_KEY_MISSING_FOR_VALIDATION": {
        "tr": "Doğrulamak için lütfen önce bir API anahtarı girin.",
        "en": "Please enter an API key first to validate."
    }
}

def translate(key: str, lang: str = "tr") -> str:
    """Mesajı dile göre döndürür, bulunamazsa key'i döndürür."""
    if lang not in ["tr", "en"]:
        lang = "tr"
    
    msg_dict = MESSAGES.get(key)
    if not msg_dict:
        return key
    
    return msg_dict.get(lang, msg_dict.get("tr", key))
