# Worker Başlatma Hatası ve "Stopped" Durumu Çözümü (03 Mayıs 2026)

## Sorun Tanımı
`fly deploy` yapılmasına rağmen `fly status` çıktısında worker makinelerinin `stopped` (durdurulmuş) olarak görünmesi ve sınavların "Bekliyor"da kalması.

---

## Tespit Edilen Neden: Asyncio Loop Çakışması
Fly.io üzerindeki Python paketleri arasında `uvloop` bulunmaktadır. Celery worker başladığında otomatik olarak `uvloop` politikasını aktif eder. Ancak bizim kodumuz (hem sınav üretimi hem puanlama) `asyncio.run()` komutunu kullanmaktadır.

**Hata Mekanizması:**
1. Worker başlar ve `uvloop` event loop'unu hazırlar.
2. İlk görev (task) geldiğinde `asyncio.run()` çağrılır.
3. `asyncio.run()` mevcut (running) bir loop varken çalıştırılamaz hatası verir.
4. Worker süreci bu kritik hata yüzünden çöker (crash) ve Fly.io makineyi durdurur.

---

## Yapılan Çözüm

### 1. Event Loop Politikası Sabitlendi
`backendWindsurf2/celery_app.py` dosyasına şu mantık eklendi:
- Eğer bu süreç bir Celery worker ise (`FORKED_BY_MULTIPROCESSING == 1`), `uvloop` politikası devre dışı bırakılır.
- Bunun yerine standart `asyncio.DefaultEventLoopPolicy()` zorlanır.
- Bu sayede `asyncio.run()` komutu temiz bir ortamda çalışabilir hale gelir.

### 2. Puanlama Görevi Refactor (Daha Önce Yapıldı)
`grade_quiz_task` fonksiyonu, iç içe (nested) closure yerine üst seviye bir async fonksiyonu (`run_quiz_grading`) çağıracak şekilde güncellendi.

---

## Uygulama ve Doğrulama Adımları

1. **Deploy Et:**
   ```powershell
   cd backendWindsurf2
   fly deploy
   ```

2. **Manuel Başlatma (Eğer hala stopped ise):**
   Eğer deploy sonrası hala duruyorsa, Fly.io'ya makineyi zorla başlatması komutunu ver:
   ```powershell
   fly machine start 0803d27a693908
   ```

3. **Log Takibi:**
   ```powershell
   fly logs
   ```
   Loglarda `Disabled uvloop policy for Celery worker` satırını görmelisin.

---

## Özet
Bu düzenleme ile worker'ın çökmesine neden olan "Event loop already running" hatasının kökü kurutulmuştur. Sistem artık Fly.io ortamında Celery ile uyumlu bir asenkron döngü kullanmaktadır.
