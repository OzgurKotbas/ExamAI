# Kullanıcı API Anahtarı Önceliklendirme

Bu döküman, ExamAI platformunda kullanıcıya ait Gemini API anahtarının çalışma hiyerarşisindeki yerini açıklar.

## Çalışma Mantığı

Sistem, sınav oluşturma ve notlandırma süreçlerinde aşağıdaki sırayı (Hiyerarşi) takip eder:

1.  **Birincil Öncelik (User API Key):** Eğer kullanıcının profilinde kayıtlı bir Gemini API anahtarı varsa, sistem Hugging Face modellerini ve sistem varsayılan anahtarını **atlayarak** doğrudan kullanıcının anahtarını kullanır.
2.  **İkincil Seçenek (Hugging Face):** Kullanıcının API anahtarı yoksa veya çalışmıyorsa, sistem `config.py` içinde tanımlı olan Hugging Face modellerini (Qwen, Mistral vb.) sırayla dener.
3.  **Son Çare (System Gemini Key):** HF modelleri de yanıt vermezse, sistem geliştiricinin tanımladığı varsayılan Gemini anahtarını kullanarak işlemi tamamlamaya çalışır.

## Yapılan Değişiklikler

### `backendWindsurf2/services/ai_service.py`
- `_generate_with_fallback` fonksiyonu, `user_api_key` parametresini en üst önceliğe alacak şekilde güncellendi.
- Kullanıcı anahtarı bulunduğu takdirde loglarda `User-provided Gemini API key found. Using it as primary provider.` mesajı görünür.

## Avantajları
- **Hız:** Kullanıcı anahtarı varken Hugging Face bekleme süreleri (cold start vb.) atlanır.
- **Kişiselleştirme:** Kullanıcı kendi kotasını ve limitlerini kullanır.
- **Tutarlılık:** Gemini modelleri daha yüksek kaliteli JSON çıktısı ürettiği için hata payı azalır.
