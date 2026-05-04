# Yapay Zeka Sağlayıcı Öncelik Güncellemesi (03 Mayıs 2026)

## Değişiklik Özeti
Yapay zeka modellerinin (soru üretimi ve puanlama) çalışma önceliği kullanıcı isteği üzerine değiştirilmiştir.

**Eski Mantık:**
1. Gemini API (Birincil)
2. Hugging Face Modelleri (Yedek)

**Yeni Mantık:**
1. **Hugging Face Modelleri (Birincil)**
2. **Gemini API (Yedek)**

## Detaylar
- **Dosya:** `backendWindsurf2/services/ai_service.py`
- `_generate_with_fallback` fonksiyonu güncellendi.
- Sistem artık önce `HUGGINGFACE_API_TOKENS` içindeki tokenları ve `HUGGINGFACE_MODELS` içindeki modelleri sırayla dener.
- Eğer tüm Hugging Face denemeleri başarısız olursa (Rate limit, timeout vb.), sistem otomatik olarak `GEMINI_API_KEY` kullanarak Gemini modeline geçer.

## Uyarı
Hugging Face modellerinin cevap süresi Gemini'ye göre daha uzun olabilir. Bu durum sınav sonuçlarının hesaplanma süresini bir miktar artırabilir. Ancak sistem her zaman en sonunda Gemini'ye dönerek cevabın mutlaka üretilmesini garanti eder.

## Uygulama Adımları
Bu değişikliğin aktif olması için backend tarafının deploy edilmesi gerekmektedir:
```powershell
cd backendWindsurf2
fly deploy
```
