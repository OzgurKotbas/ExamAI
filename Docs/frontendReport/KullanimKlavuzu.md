# ExamAI Kullanım Kılavuzu

Bu kılavuz, ExamAI platformuna nasıl giriş yapacağınızı ve temel özellikleri nasıl kullanacağınızı adım adım açıklar.

---

## 📋 İçindekiler

1. [Sisteme İlk Kez Giriş (Kayıt Olma)](#1-sisteme-ilk-kez-giriş-kayıt-olma)
2. [Mevcut Hesapla Giriş](#2-mevcut-hesapla-giriş)
3. [Şifremi Unuttum - Şifre Sıfırlama](#3-şifremi-unuttum---şifre-sıfırlama)
4. [Dashboard Kullanımı](#4-dashboard-kullanımı)
5. [Google ile Hızlı Giriş](#5-google-ile-hızlı-giriş)

---

## 1. Sisteme İlk Kez Giriş (Kayıt Olma)

Yeni bir hesap oluşturmak için aşağıdaki adımları takip edin:

### Adım 1: Kayıt Sayfasına Gitme
1. Tarayıcınızda site adresine gidin: `http://localhost:5173`
2. Karşınıza çıkan ekranda **"Kayıt Ol"** bağlantısına tıklayın
   - Alternatif: Doğrudan `/register` sayfasına gidin

### Adım 2: Bilgileri Doldurma
Kayıt formunda aşağıdaki bilgileri eksiksiz doldurun:

| Alan | Açıklama | Örnek |
|------|----------|-------|
| **Ad Soyad** | Gerçek adınızı girin | Ahmet Yılmaz |
| **E-posta Adresi** | Geçerli bir e-posta adresi | ahmet@email.com |
| **Şifre** | En az 6 karakterli güçlü şifre | ******** |
| **Şifre Tekrar** | Şifrenizi tekrar girin | ******** |

> ⚠️ **Önemli:** Şifre ve şifre tekrarı alanları eşleşmelidir!

### Adım 3: Kayıt İşlemini Tamamlama
1. Bilgileri kontrol edin
2. **"Kayıt Ol"** butonuna tıklayın
3. Başarılı kayıt sonrası otomatik olarak giriş yapılacak ve Dashboard'a yönlendirileceksiniz

---

## 2. Mevcut Hesapla Giriş

Daha önce kaydolduysanız, giriş yapmak için:

### Adım 1: Giriş Sayfasına Gitme
1. Site adresine gidin: `http://localhost:5173`
2. Sistem otomatik olarak giriş sayfasına yönlendirecektir
   - Alternatif: Doğrudan `/login` sayfasına gidin

### Adım 2: Giriş Bilgilerini Girme
Giriş formunda istenen bilgileri doldurun:

| Alan | Açıklama | Örnek |
|------|----------|-------|
| **E-posta Adresi** | Kayıtlı e-posta adresiniz | ahmet@email.com |
| **Şifre** | Hesap şifreniz | ******** |

### Adım 3: Giriş Yapma
1. Bilgilerinizi kontrol edin
2. **"Giriş Yap"** butonuna tıklayın
3. Başarılı giriş sonrası Dashboard'a yönlendirileceksiniz

> 💡 **İpucu:** Şifrenizi görmek için şifre alanındaki göz ikonuna tıklayabilirsiniz.

---

## 3. Şifremi Unuttum - Şifre Sıfırlama

Şifrenizi unuttuysanız, 2 adımlı süreçle yeni şifre belirleyebilirsiniz:

### Adım 1: Şifre Sıfırlama İsteği
1. Giriş sayfasında **"Şifremi Unuttum"** bağlantısına tıklayın
2. Açılan sayfada kayıtlı **e-posta adresinizi** girin
3. **"Kod Gönder"** butonuna tıklayın
4. E-posta adresinize 6 haneli doğrulama kodu gönderilecektir

> ⏱️ **Kod Geçerlilik Süresi:** 10 dakika

### Adım 2: Doğrulama Kodu ve Yeni Şifre
1. E-posta kutunuzu kontrol edin (Spam klasörünü de kontrol edin!)
2. Gelen 6 haneli kodu ekrandaki **"Doğrulama Kodu"** alanına girin
3. **Yeni Şifre** belirleyin (en az 6 karakter)
4. **Yeni Şifre Tekrar** alanına aynı şifreyi girin
5. **"Şifreyi Sıfırla"** butonuna tıklayın

### Adım 3: Giriş Yapma
Şifre başarıyla sıfırlandıktan sonra:
1. **"Giriş Yap"** butonuna tıklayın
2. Yeni şifrenizle giriş yapın

---

## 4. Dashboard Kullanımı

Giriş yaptıktan sonra Dashboard ekranında şunları yapabilirsiniz:

### 4.1 İstatistikleri Görüntüleme
Dashboard üst kısmında 3 kart göreceksiniz:
- **Yüklenen Kaynak:** Kaç ders notu yüklediğiniz
- **Oluşturulan Sınav:** Kaç sınav oluşturduğunuz
- **Tamamlanan:** Kaç sınavı tamamladığınız

### 4.2 Yeni Kaynak Yükleme
1. **"Yeni Sınav Oluştur"** sekmesine tıklayın
2. **"Kaynak Yükle"** bölümünden:
   - Dosyayı sürükleyip bırakın, veya
   - Alanı tıklayıp dosya seçin
3. Desteklenen formatlar: PDF, JPG, PNG, TXT (max 20MB)
4. **"Yükle ve İşle"** butonuna tıklayın

### 4.3 Sınav Oluşturma
1. Yüklediğiniz kaynaklardan birini seçin
2. **"Yapay Zeka ile Sınav Hazırlat"** butonuna tıklayın
3. Açılan pencerede ayarları yapın:
   - **Soru Sayısı:** 5-50 arası
   - **Test/Açık Uçlu Oranı:** %0-100 arası
   - **Zorluk Seviyesi:** Kolay / Orta / Zor
4. **"Sınav Oluştur"** butonuna tıklayın

### 4.4 Geçmiş Sınavları Görüntüleme
1. **"Geçmiş Sınavlar"** sekmesine tıklayın
2. Tüm sınavlarınızı kronolojik sırayla görürsünüz
3. Herhangi bir sınavı tıklayarak detaylarına gidebilirsiniz

### 4.5 Çıkış Yapma
1. Sağ üst köşedeki kullanıcı adınıza tıklayın
2. Açılan menüden **"Çıkış"** seçeneğine tıklayın

---

## 5. Google ile Hızlı Giriş

Google hesabınız varsa, hızlıca giriş yapabilirsiniz:

### Giriş veya Kayıt Sayfasında
1. **"Google ile Giriş Yap"** veya **"Google ile Kayıt Ol"** butonuna tıklayın
2. Google hesabı seçim ekranında hesabınızı seçin
3. İzinleri onaylayın
4. Sistem otomatik olarak giriş yapacak ve Dashboard'a yönlendirecektir

> ⚠️ **Not:** İlk kez Google ile giriş yapıyorsanız, sistem otomatik olarak hesabınızı oluşturur.

---

## 🔧 Sık Karşılaşılan Sorunlar

| Sorun | Çözüm |
|-------|-------|
| "Geçersiz e-posta veya şifre" | Bilgilerinizi kontrol edin, Caps Lock kapalı mı? |
| "Bu e-posta ile kayıtlı hesap var" | Giriş yapmayı deneyin veya şifre sıfırlama kullanın |
| "Şifreler eşleşmiyor" | Kayıt olurken şifre ve tekrar alanlarının aynı olduğundan emin olun |
| "Kod geçersiz veya süresi dolmuş" | Yeni kod talep edin (10 dk geçerlidir) |
| "Dosya çok büyük" | 20MB'dan küçük dosya yükleyin |
| "Desteklenmeyen dosya formatı" | Sadece PDF, JPG, PNG veya TXT yükleyin |

---

## 📞 Destek

Teknik sorun yaşarsanız:
1. Tarayıcı önbelleğini temizleyin
2. Farklı bir tarayıcı deneyin
3. İnternet bağlantınızı kontrol edin

---

**Son Güncelleme:** 5 Nisan 2026
