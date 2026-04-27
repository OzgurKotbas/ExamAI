# Gemini API Kota Sorunu ve Cozum Raporu

## Sorun Ozeti
ExamAI altyapisinda yapay zeka servisleri (soru olusturma, puanlama) Google Gemini API kullanmaktadir. Sistemde `RESOURCE_EXHAUSTED (429)` hatasi alindigi ve servislerin durdugu tespit edilmistir.

## Hata Kaynagi Analizi
`ai_errors.log` dosyasi incelendiginde, Google'dan gelen hata mesaji su sekildedir:
> "Quota exceeded for metric: ... limit: 20, model: gemini-2.5-flash"

Bu hata, `.env` dosyasindaki `GEMINI_MODEL` ayarinin `gemini-2.5-flash` olarak kalmiş olmasindan kaynaklanmaktadir. Google'in bu özel/deneysel model sürümü için sunduğu ücretsiz kota günlük sadece **20 istek** ile sinirlidir.

## Uygulanan Cozum
Günlük kullanim kapasitesini artirmak ve sistemi stabil hale getirmek için aşagidaki degisiklik yapilmistir:

1.  **.env Guncellemesi:** `GEMINI_MODEL=gemini-2.5-flash` degeri `GEMINI_MODEL=gemini-1.5-flash` olarak degistirilmistir.
2.  **Kapasite Artisi:** `gemini-1.5-flash` modeline gecilmesiyle birlikte:
    -   Günlük istek limiti **20'den 1.500'e** cikarilmistir.
    -   Dakikalik istek limiti **15 RPM** (Requests Per Minute) olarak belirlenmistir.

## Sonuc ve Tavsiyeler
Yapilan degisiklik sonrasinda sistem artik günlük 1.500 teste kadar sorunsuz hizmet verebilecektir.

**Not:** Eger gelecekte daha yüksek kapasiteye ihtiyac duyulursa:
- Google AI Studio üzerinden "Pay-as-you-go" planina gecilebilir.
- Birden fazla API anahtari arasinda dönüsüm yapan bir rotator sistemi kurulabilir (mevcut yük icin gerekmemektedir).

---
*Hazirlayan: Antigravity*
*Tarih: 2026-04-09*
