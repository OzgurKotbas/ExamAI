# Gemini API Model Keşfi ve Genişletilmiş Uyumluluk

Bu döküman, tüm model isimlerinin 404 hatası vermesi durumunda devreye alınan "Tam Kapsamlı Kurtarma" sistemini açıklar.

## Sorun Analizi
Yapılan testlerde `gemini-1.5-flash`, `gemini-pro` gibi standart isimlerin tamamının 404 hatası döndürdüğü görülmüştür. Bu durum, API anahtarının bağlı olduğu projenin sadece belirli (veya yeni nesil `latest`) isimleri kabul ettiğini göstermektedir.

## Yapılan Değişiklikler

### 1. `backendWindsurf2/services/ai_service.py`
- **Genişletilmiş Model Listesi:** Denenecek model sayısı 10'un üzerine çıkarıldı (`gemini-1.5-flash-latest`, `gemini-1.5-pro-002` vb.).
- **Dinamik Keşif (Dynamic Discovery):** Eğer listedeki hiçbir model çalışmazsa, sistem `genai.list_models()` komutunu kullanarak o API anahtarı için tanımlı tüm modelleri sorgular.
- **Çift Versiyon Desteği (v1 & v1beta):** Sistem artık sadece tek bir API sürümüne bağlı kalmaz. Önce `v1beta` üzerinden tüm modelleri dener, başarısız olursa otomatik olarak `v1` sürümüne geçerek tüm süreci tekrarlar.
- **Versiyon Toleransı:** SDK'nın model isimlerini `models/` ön ekiyle veya ekiz olarak denemesi sağlandı.

## Uygulama ve Kontrol
Sistem artık hata vermek yerine "bulana kadar ara" mantığıyla çalışacaktır. Eğer API anahtarı tamamen geçersizse, bu durum artık `invalid api key` olarak net bir şekilde loglanacaktır.

VS Code üzerinden `start_all.bat` çalıştırıldıktan sonra sistem ilk sınav denemesinde en uygun modeli otomatik olarak seçecektir.
