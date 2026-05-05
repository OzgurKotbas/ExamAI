# Gemini Bağlantı ve 503 (Service Unavailable) Çözümü

Bu döküman, Gemini API çağrılarında yaşanan 404 (Not Found) ve 503 (Service Unavailable) hatalarını gidermek için yapılan teknik değişiklikleri özetler.

## Yapılan Değişiklikler

### 1. `backendWindsurf2/services/ai_service.py`
*   **Model İsimlendirme Formatı:** Tüm model isimlerine (`gemini-1.5-flash` vb.) SDK'nın beklediği `models/` ön eki açıkça eklendi. Bu, özellikle 2026 yılındaki güncel API endpoint'lerinde yaşanan 404 hatalarını engeller.
*   **503 ve 500 Hata Yönetimi:** Google sunucularından dönen "Service Unavailable" (503) ve "Internal Server Error" (500) hataları artık "geçici hata" olarak kabul ediliyor. Sistem bu hataları aldığında pes etmek yerine **Exponential Backoff** (katlanarak artan bekleme süresi) ile tekrar deneme yapıyor.
*   **Transport Katmanı:** İstikrarı artırmak için `transport="rest"` zorlaması kaldırıldı. SDK'nın en kararlı bağlantı yöntemini (varsayılan gRPC) otomatik seçmesine izin verildi.
*   **Akıllı Model Keşfi (Discovery):** Proje 2026 yılında geçtiği için `list_models()` ile dönen yeni nesil modeller (Gemini 2.5, 3.0 vb.) artık daha güvenli bir şekilde taranıyor. Kararsız olabilecek "thinking" veya "experimental" modeller filtrelendi.

## Neden Yapıldı?
*   **404 Hatası:** SDK versiyonu ile Google'ın isimlendirme standartları arasındaki uyumsuzluktan kaynaklanıyordu.
*   **503 Hatası:** Yeni nesil modellerin (Gemini 3 vb.) bazen yoğunluktan dolayı cevap verememesinden kaynaklanıyordu. Yeniden deneme mekanizması bu kesintileri kullanıcıya hissettirmeden aşmayı sağlar.

## Değişen Dosyalar
*   `backendWindsurf2/services/ai_service.py`: Ana bağlantı ve hata yakalama mantığı güncellendi.

## Sonraki Adımlar
1.  **Sistemi Yeniden Başlat:** `start_all.bat` dosyasını kullanarak tüm servisleri ve Celery Worker'ı tazeleyin.
2.  **Test Et:** Sınav oluşturma butonuna basın. Loglarda `Retryable error (ServiceUnavailable)` görseniz bile sistemin otomatik olarak bekleyip tekrar denediğini ve sonunda başarılı olduğunu göreceksiniz.
