# ExamAI Sınav Üretimi Gecikmesi: Sorun Giderme (Troubleshooting) Rehberi

**Tarih:** 06.04.2026 - 13:35
**Raporu Hazırlayan:** Antigravity (Sistem Ajanı)

Eğer bir sınavı oluştur butonuna bastıktan sonra 3 dakika geçmesine rağmen ekranınızda hala "Sınav Bekleniyor/Oluşturuluyor" (Pending/Generating) yazıyorsa, backend ile frontend arasında veri alışverişinin kopmuş olmasından ziyade **Arka Plan İşlem Motorunda (Celery / Redis / Gemini)** bir tıkanıklık söz konusudur. 

Aşağıda bu sorunun en yaygın 4 nedeni ve anında çözüm yolları sıralanmıştır:

---

## 1. Redis Sunucusu Çalışmıyor Olabilir (En Yaygın Sebep)

ExamAI arka ucu, sınav üretim emirlerini sıraya dizmek (Queue) için **Redis** veritabanına muhtaçtır. Eğer bilgisayarınızda Redis o an kapalıysa, Celery mesajı alamaz ve quiz işlemi veritabanında sonsuza kadar `pending` (bekliyor) olarak asılı kalır.

**Çözüm Yolu:**
- Docker kullanıyorsanız uygulamasından Redis konteynerinin çalışıp çalışmadığını kontrol edin.
- Windows Subsystem (WSL) kullanıyorsanız başlat menüsünden WSL/Ubuntu açıp `redis-server` komutunu çalıştırın.
- Redis'in 6379 portunda çalıştığından emin olun.

## 2. Celery Worker (Yapay Zeka İşçisi) Kapanmış Veya Çökmüş Olabilir

Başlatma scriptiyle açılan siyah ekranlardan `Celery Worker` log ekranında kırmızı hata var mı diye kontrol etmelisiniz. Eğer worker çalışmıyorsa görevleri işleyecek kimse yoktur.

**Çözüm Yolu:**
- `start_all.bat` dosyasının açtığı Celery adlı CMD penceresini ekrana getirin.
- Ekran boş duruyorsa pencereye bir kez tıklayıp **"Enter"** tuşuna basın. (Windows bazen konsol içine tıklanınca işlemleri pause durumuna/beklemeye alır. Enter'a basınca asılı kalan yazılar akmaya başlayıp sınavınız hemen oluşabilir).
- Eğer o CMD kapatıldıysa yeniden başlatmanız gerekir.

## 3. Gemini (Google AI) API Anahtarı veya Kota Sorunu

Celery görevi üzerine almış ama Google'ın yapay zeka sunucularına ulaştığında kırmızı ışık yemiş olabilir.

**Çözüm Yolu:**
- `backendWindsurf2/.env` dosyanıza girerek `GEMINI_API_KEY` değerinin dolu olduğunu ve geçerliliğini koruduğunu teyit edin.
- Ücretsiz katmanlarda dakikada 15 istek sınırı vardır. Celery loglarında (Siyah CMD penceresi) `429 Too Many Requests` veya `401 Unauthorized` tarzı bir yazı görüyorsanız sorun tamamen Google tarafındadır.

## 4. Belge Çok Kısa Şifrelenmiş (Decryption Error)

Eğer yüklediğiniz PDF veya Not içeriği çok kısa, fotoğraf şeklindeyse veya OCR veritabanına "boş" olarak (şifreleme hatası ile) yansıdıysa, kodumuz 50 karakter altındaki metinlerde sınav ürettirmemek üzere programlanmıştır. Fakat arka planda hata fırlattığı için frontend takılı görülebilir.

**Çözüm Yolu:**
- O notu tamamen silin (Klasör yanındaki yeni eklediğimiz çöp kutusu özelliğiyle).
- İçinde saf metin olduğuna emin olduğunuz net bir PDF yükleyip tekrar sıfırdan "Sınav Başlat" diyin.

---

### 👉 Ne Yapmalısınız?
Lütfen açık olan 3 adet siyah komut (CMD) penceresine sırayla görev çubuğundan tıklayıp her birinin içine bir kere tıklayarak **ENTER** tuşuna basınız. Çoğu Windows makinesinde terminal seçiliyince donma yaşanır. Ardından Celery terminalinde herhangi bir "ERROR" (Kırmızı hata) yazısı olup olmadığını kontrol ediniz. Hala çözülmezse Redis'inizi başlatmanız zorunludur.
