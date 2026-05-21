# Gemini Model Dropdown & API Key Doğrulama — Değişiklik Raporu
**Tarih:** 20 Mayıs 2026  
**Konu:** Kullanıcı profili ekranında model ismi seçimi ve API anahtarı doğrulaması

---

## Neden Bu Değişiklik Yapıldı?

Daha önce kullanıcılar Gemini model ismini boş bir metin kutusuna elle yazıyordu. Bu durum şu sorunlara yol açıyordu:

- Kullanıcı `gemini-1.5-flash` yerine `gemini 1.5 flash` veya `flash` yazabiliyordu → **404 Model Bulunamadı hatası**
- Hangi modellerin var olduğunu bilmek zorunda kalınıyordu.
- API anahtarının geçerli olup olmadığını test etme imkânı yoktu; sorun ancak sınav oluşturulurken ortaya çıkıyordu.

---

## Yapılan Değişiklikler

### 1. `backendWindsurf2/services/ai_service.py`

**Eklenenler:**
- `SUPPORTED_GEMINI_MODELS` listesi: Frontend dropdown için desteklenen 7 modelin Python listesi.
- `validate_gemini_api_key(api_key, model_name, lang)` async fonksiyonu:
  - Google'ın `v1beta` REST API'sine `maxOutputTokens: 1` ile minimal bir test isteği gönderir.
  - HTTP durum koduna göre şu mesaj anahtarlarından birini döndürür:
    | Durum Kodu | Mesaj Anahtarı |
    |---|---|
    | 200 | `GEMINI_KEY_VALID` |
    | 401 / 403 | `GEMINI_KEY_INVALID` |
    | 404 | `GEMINI_MODEL_NOT_FOUND` |
    | 429 | `GEMINI_QUOTA_EXCEEDED` |
    | Bağlantı hatası | `GEMINI_CONNECTION_ERROR` |
    | Diğer | `GEMINI_VALIDATION_FAILED` |

---

### 2. `backendWindsurf2/utils/i18n.py`

**Eklenenler:** 7 yeni mesaj anahtarı (Türkçe + İngilizce):
- `GEMINI_KEY_VALID`
- `GEMINI_KEY_INVALID`
- `GEMINI_MODEL_NOT_FOUND`
- `GEMINI_QUOTA_EXCEEDED`
- `GEMINI_CONNECTION_ERROR`
- `GEMINI_VALIDATION_FAILED`
- `GEMINI_KEY_MISSING_FOR_VALIDATION`

---

### 3. `backendWindsurf2/routers/auth.py`

**Eklenenler:** 2 yeni endpoint

#### `GET /api/v1/auth/gemini-models`
- Kimlik doğrulama gerektirmez.
- Desteklenen Gemini modellerinin listesini JSON olarak döndürür.
- Kullanım: `{ "models": ["gemini-2.5-flash-preview-05-20", ...] }`

#### `POST /api/v1/auth/validate-gemini-key`
- Kimlik doğrulama gerektirir (Bearer token).
- Form alanları: `gemini_api_key`, `gemini_model`
- `v1beta` altyapısı üzerinden 1-token test isteği atar.
- Yanıt: `{ "valid": true/false, "message": "Kullanıcıya gösterilecek mesaj" }`
- Hata türüne ve kullanıcı diline (`X-Language` header) göre mesaj döner.

---

### 4. `examai-frontend/src/api/index.js`

**Eklenenler:** `authApi` nesnesine 2 yeni fonksiyon:

```js
authApi.getGeminiModels()          // GET /auth/gemini-models
authApi.validateGeminiKey(key, model)  // POST /auth/validate-gemini-key
```

---

### 5. `examai-frontend/src/components/ProfileMenu.jsx` — `AccountModal` bileşeni

**Değiştirilen:** Model ismi metin kutusu → Tıklanabilir `<select>` dropdown

**Desteklenen modeller (dropdown listesi):**
| Değer | Gösterilen Etiket |
|---|---|
| `gemini-2.5-flash-preview-05-20` | Gemini 2.5 Flash Preview ✨ (En Yeni) |
| `gemini-2.5-pro-preview-05-06` | Gemini 2.5 Pro Preview 🧠 (Güçlü) |
| `gemini-2.0-flash` | Gemini 2.0 Flash ⚡ (Hızlı) |
| `gemini-2.0-flash-lite` | Gemini 2.0 Flash Lite 🪶 (Ekonomik) |
| `gemini-1.5-flash` | Gemini 1.5 Flash ⚡ (Önerilen) |
| `gemini-1.5-flash-8b` | Gemini 1.5 Flash 8B 🪶 (Hafif) |
| `gemini-1.5-pro` | Gemini 1.5 Pro 🧠 (Gelişmiş) |

**Eklenen: "API Anahtarı & Modeli Doğrula" butonu**
- Düzenleme modu açıkken görünür.
- API anahtarı boşsa tıklanamaz (`disabled`).
- Tıklandığında `/validate-gemini-key` endpoint'ini çağırır.
- Yanıta göre renkli durum bandı gösterir:
  - 🟢 Yeşil: Başarılı doğrulama
  - 🟡 Sarı: Uyarı (kota aşımı, model erişilemez)
  - 🔴 Kırmızı: Hata (geçersiz anahtar, bağlantı hatası)
- API anahtarı veya model değiştirildiğinde mevcut doğrulama sonucu sıfırlanır.
- Doğrulama opsiyoneldir; kaydetmeden önce zorunlu değildir.

**İptal butonu davranışı güncellendi:**
- Düzenleme modunda "İptal" tüm alanları eski değerlerine geri döndürür.
- Düzenleme modu kapalıysa "İptal" modalı kapatır.

---

## Mimari Not

Altyapı olarak `v1beta` REST API tercih edildi. Bunun nedeni:
- Tüm API anahtarları `v1beta` ile çalışır (sürüm anahtara değil isteğe bağlıdır).
- En yeni modeller (Gemini 2.0, 2.5 vb.) önce `v1beta`'da yayınlanır.
- Mevcut `ai_service.py`'daki `_call_gemini_with_retry` fonksiyonu da zaten `v1beta`'yı öncelikli deniyor.

---

## Değiştirilmeyen Akışlar

- Mevcut otomatik model keşfetme ve veritabanına kaydetme mekanizması (auto-cache) korundu.
- Doğrulama başarısız olsa bile kullanıcı kayıt yapabilir; sistem yine de çalışan modeli otomatik bulur.
- `auth_service.py::update_user_profile` fonksiyonu değiştirilmedi.
