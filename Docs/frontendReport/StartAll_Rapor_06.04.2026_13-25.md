# ExamAI Başlatma Otomasyonu (start_all.bat) Raporu

**Rapor Tarihi ve Saati:** 06.04.2026 - 13:25
**Konum:** `EXAM_AI/start_all.bat`
**Mimari Entegrasyon:** Auto-Startup Script

## 1. Otomasyonun Sağladığı Avantajlar

ExamAI projesinin mimarisi hem Next nesil bir frontend uygulamasını (Vite/React) hem de arka planda yapay zeka gücünü kullanan çoklu backend işçilerini (Uvicorn FastAPI ve Celery) barındırmaktadır. Bu modüllerin her geliştirme seansında tek tek terminal açılarak başlatılması büyük bir iş gücü ve zaman kaybı teşkil ediyordu.

Yazılan `start_all.bat` sistemi sayesinde tek bir tıklama ile bu modüler yapı tamamen otomatikleştirilmiş ve 5 saniye içerisinde sistemi kullanıma hazırlayan "Tümleşik Başlatıcı (All-in-One Launcher)" mekanizması kurgulanmıştır.

## 2. Sistemin Çalışma (Tetiklenme) Mantığı

Bat dosyası üzerine çift tıklandığında aşağıdaki rotalarda komutlar çalıştırılır:

1. **Adım [1/3] Backend Aktivasyonu:** 
   Oto-Betik `backendWindsurf2` klasörüne girer, projeye has korumalı `.venv` (sanal ortamı) aktif eder ve **FastAPI/Uvicorn** sunucusunu ayağa kaldırır. Bu esnada açılan bağımsız konsol penceresi logları takip edebilmeniz için açık bırakılır.
2. **Adım [2/3] Asenkron AI (Celery) Aktivasyonu:** 
   Eşzamanlı ikinci bir konsol penceresini açar. Windows sistemlerinde Celery fork işlemlerinin `multiprocessing` hataları verdirmesini önlemek amacıyla özel bir Windows bayrağı olan `--pool=solo` etiketini iliştirerek yapay zekanın arkaplan robotunu servise sunar.
3. **Adım [3/3] Frontend (Kullanıcı Arayüzü) Aktivasyonu:** 
   Sistemin `examai-frontend` adlı arayüz klasöründe **Vite** test yayınına çıkmasını (`npm run dev`) sağlayarak 5173 nolu adresten projeyi dış dünyaya açar.
4. **Adım [Otomatik Yönlendirme]:** 
   Tüm motorların belleğe yüklenebilmesi, modüller arası bağın (Redis/Celery) çökmemesi için işletim sisteminden 5 saniyelik bir gecikme (Timeout) koparır. Ardından sorunsuzca hazır olan sistemi açmak için işletim sisteminizin varsayılan web tarayıcısını doğrudan `http://localhost:5173` adresinden başlatarak vizyona çıkarır.

## 3. Kapanış / Yeniden Başlatma

Açılan paneller ve tarayıcı üzerinde işlemlerinizi/testlerinizi durdurmak istediğinizde ekstra bir işlem veya komut yazmanıza gerek yoktur. İşletim sistemindeki siyah konsol komut pencerelerini sağ üstteki ❌ işaretinden kapattığınızda otomatik yayın kesilir.
