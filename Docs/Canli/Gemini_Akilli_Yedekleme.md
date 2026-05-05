# Gemini Akıllı Model Yedekleme (Smart Fallback) Sistemi

Bu döküman, Gemini API çağrılarında yaşanan "404 Not Found" hatalarını önlemek için devreye alınan yeni sistemi açıklar.

## Sorun
Bazı API anahtarları veya bölgeler, `gemini-1.5-flash` modelini desteklemeyebilir veya farklı bir isimlendirme bekleyebilir. Bu durum, işlemin 1 dakika bekledikten sonra 404 hatasıyla sonuçlanmasına neden oluyordu.

## Yapılan Değişiklikler

### `backendWindsurf2/services/ai_service.py`
- `_call_gemini_with_retry` fonksiyonuna **Model Fallback** (Model Yedekleme) mantığı eklendi.
- Sistem artık tek bir modele bağlı kalmak yerine şu sırayı takip eder:
    1.  `.env` içinde tanımlı ana model (örn: `gemini-1.5-flash`)
    2.  `gemini-1.5-flash` (SDK uyumlu isim)
    3.  `gemini-1.5-pro` (Daha gelişmiş yedek model)
    4.  `gemini-pro` (Klasik kararlı model)

## Nasıl Çalışır?
- Eğer ilk denemede 404 hatası alınırsa, sistem bunu loglara kaydeder (`Gemini model X not found (404)`) ve hemen listedeki bir sonraki modeli dener.
- Bu işlem, listedeki tüm modeller tükenene kadar devam eder.
- Böylece kullanıcının API anahtarı hangi modeli destekliyorsa, sistem onu otomatik olarak bulur ve sınavı oluşturur.

## Avantajları
- **Kesintisiz Deneyim:** Kullanıcının model isimleriyle uğraşmasına gerek kalmaz.
- **Hata Toleransı:** Bölgesel veya hesap bazlı model kısıtlamaları otomatik olarak aşılır.
- **Görünürlük:** Hangi modelin çalıştığı veya hangisinin hata verdiği backend loglarından takip edilebilir.

## VS Code İşlemleri
1.  Değişiklikleri kaydedin:
    ```powershell
    git add .
    git commit -m "Gemini akıllı model yedekleme sistemi eklendi"
    ```
2.  Sistemi `start_all.bat` ile yeniden başlatın.
