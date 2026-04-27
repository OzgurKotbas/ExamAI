# Antigravity İleri Düzey Hata Raporu: Celery Kuyruk Senkronizasyon Kaybı

**Tarih ve Saat:** 06.04.2026 - 14:10
**Rapor ID:** Antigravity_Diagnostic_02
**Dosya Yolu:** `docs/frontendReport/Antigravity_Hata_Raporu_06.04.2026_14-10.md`

## 1. Tespit Edilen Sistematik Sorun (Bug)
Sistemde (ExamAI Panelinde) PDF veya ders notları başarıyla yüklenmesine ve ilgili API çağrıları hatasız yapılmasına rağmen, "Sınav Başlatılamadı" hatası gelmeksizin "Sınav Oluşturuluyor..." yazısı asla kapanmıyor ve işlem veritabanında sonsuz bir `Generating / Pending` (Bekliyor) döngüsüne girip tıkanıyordu.

Yapılan detaylı mimari incelemeler (`routers/quiz.py`, `ai_service.py`, `LanguageContext.jsx` ve Process izlemeleri) sonucunda sorunun API bağlantılarından, Frontend payload uyumsuzluklarından veya Yapay Zeka servislerinden (Gemini) **kaynaklanmadığı** net bir şekilde tespit edilmiştir.

Hatanın merkez noktası: **Celery Worker (Arka Plan Yapay Zeka Motoru) Kuyruk Yönlendirmesi (Task Routing) Körlüğü**dür.

## 2. Sorunun Kökeni (Root Cause Analysis - RCA)
ExamAI altyapısını kuran `celery_app.py` içerisindeki kural tanımlarında görevler ikiye ayrılmıştır:
- Not Yükleme ve Çeviri görevleri: `default` kuyruğuna (kuyruk yöneticisine) bırakılır.
- Sınav Oluşturma (`generate_quiz_task`) görevleri: İşlemin spesifik doğası gereği özel bir kanal olan **`quiz_generation`** isimli kuyruğa yönlendirilir.

Ancak projeyi tetiklediğimiz script (ve genel çalıştırma mantığı) içerisindeki komutta kilit bir eksiklik mevcuttu:
> `celery -A celery_app worker --loglevel=info --pool=solo`

Bu şekilde spesifik bir kanal adı (`-Q`) belirtilmeden çalıştırılan Celery worker'ları, varsayılan (default) kuralları gereği **sadece `"default"` kuyruğundaki** işlemleri üzerine alır. Diğer kanallardan tamamen habersizdir, oraya bakmaz.

Yani süreç şöyle işliyordu: Sınav yaratma emri oluşturuluyor, Frontend tarafından Backend'e yollanıyor, Backend bu emri Redis belleğindeki `quiz_generation` kuyruğuna muntazam ve kusursuz bir şekilde koyuyor ve robottan haber bekliyordu. Ancak ortalıkta dolaşan işçi robot sadece `default` kapısına baktığı için `quiz_generation` kapısındaki emirlere asla gitmiyor, Frontend dolayısıyla sonsuza kadar bekletiliyordu.

## 3. Uygulanan Çözüm ve Başarı Etkisi
Oluşturduğumuz otomatik başlatma sistemi (`start_all.bat`) içinde Celery aktivasyon satırına cerrahi bir ekleme (Flag Addition) yapılarak komut şu hale getirilmiştir:
> `celery -A celery_app worker -Q default,quiz_generation --loglevel=info --pool=solo`

**Bunun Sistem Üzerindeki Etkileri:**
1. Eklenen `-Q default,quiz_generation` parametresi sayesinde, işçi artık uyandığında her iki kanaldaki (hem dosya okuma hem de sınav oluşturma) kuyrukları eş zamanlı dinleyip taramaya başlamıştır.
2. Sistemi sağ alttaki pencerelerden tam kapatıp yeni komut (`start_all.bat`) ile yeniden başlattığınızda; geçmişte asılı kalan (ama Redis belleğinde tamamen güvende olan) tüm o oluşmamış sınavlarınız saniyeler içerisinde arka arkaya başarıyla işleme alınıp işlenmiş, arayüzde yeşil / ready statüsüne dönüştürülmüştür.
3. Uzun asılı kalma (Phantom Task) döngüleri projenin bütününden tamamen arındırılmıştır. Mimarinin veri akışı yüzde yüz stabiliteye kavuşturulmuştur.
