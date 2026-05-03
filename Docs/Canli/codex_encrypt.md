# Canli Dosya Yukleme Sifreleme Duzeltmesi

Tarih: 2026-04-30

## Yeni Log Bulgusu

Upload istegi artik PDF metin cikarima kadar ilerliyor. Hata sifreleme adiminda:

```text
Error encrypting text: NOTE_ENCRYPTION_KEY is not valid base64: Incorrect padding
Metin sifreleme hatasi (...pdf): Failed to encrypt text
POST /api/v1/notes HTTP/1.1" 400 Bad Request
```

Bu, dosya isleme/PDF okuma probleminin asil engel olmadigini; canli `NOTE_ENCRYPTION_KEY` degerinin base64 formatinda gecersiz oldugunu gosterir.

## Ek Log Bulgusu

Google login sirasinda ayrica su hata goruldu:

```text
value too long for type character varying(512)
UPDATE users SET picture_url=...
```

Google profil resmi URL'si veritabanindaki `picture_url` kolon limitini asiyor.

## Yapilan Degisiklikler

- `backendWindsurf2/utils/security.py`
  - `NOTE_ENCRYPTION_KEY` gecersiz base64 ise ve `SECRET_KEY` gecerliyse not sifreleme anahtari `SECRET_KEY` uzerinden turetiliyor.
  - Boylece canli ortamda yanlis formatli note key dosya yuklemeyi dusurmuyor.

- `backendWindsurf2/main.py`
  - `/health` artik `note_encryption_key` icin sadece var/yok degil, gercekten 32 byte base64 decode edilebilir mi kontrol ediyor.
  - `note_encryption_fallback` alani eklendi. Bu alan `true` ise note key gecersiz ama `SECRET_KEY` ile fallback calisabilir demektir.

- `backendWindsurf2/services/auth_service.py`
  - Google `picture_url` 512 karakterden uzunsa DB'ye yazilmiyor.
  - Google login akisini profil resmi URL uzunlugu yuzunden dusuren hata engellendi.

## .env ve Fly Secrets Notu

Canli Fly deployment `.env` dosyasini kullanmaz; canli degerler `fly secrets` uzerinden gelir. Bu yuzden yereldeki `.env` icindeki `SECRET_KEY` ile Fly'daki `SECRET_KEY` farkli olabilir.

Yerel testlerde ayni token/anahtar davranisini istiyorsan `.env` degerini Fly'a verdigin degerle esitleyebilirsin. Canli sistem icin zorunlu olan Fly secrets'tir.

## Kalici Tavsiye

Kod fallback ekledi, fakat en temiz cozum `NOTE_ENCRYPTION_KEY` degerini dogru base64 32 byte olarak yeniden set etmektir:

```powershell
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
$noteKey = [Convert]::ToBase64String($bytes)
fly secrets set NOTE_ENCRYPTION_KEY=$noteKey
```

Sonra:

```powershell
fly deploy --no-cache
```

Deploy sonrasi `https://backendwindsurf2.fly.dev/health` icinde:

```json
"note_encryption_key": true
```

gorunmelidir.

