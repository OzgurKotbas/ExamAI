# Canli Auth Hata Analizi ve Duzeltme Notu

Tarih: 2026-04-30

## Incelenen Belirtiler

- Canli frontend: `https://exam-ai-xi.vercel.app/register`
- Canli backend health: `https://backendwindsurf2.fly.dev/health`
- Health cevabi: `{"status":"healthy","app_name":"ExamAI","environment":"development"}`
- Google girisi: `https://backendwindsurf2.fly.dev/api/v1/auth/google` canlida `500` donuyor.
- Kayit endpoint testi: `/api/v1/auth/register` canlida `{"detail":"Failed to hash password"}` donuyor.

## Kok Nedenler

1. `passlib[bcrypt]==1.7.4` kullaniliyor fakat `bcrypt` surumu sabitlenmemisti. Deploy sirasinda uyumsuz yeni `bcrypt` surumu kurulunca `hash_password()` kiriliyor. Bu, kayit formunda `Failed to hash password` hatasina neden oluyor.

2. Login akisi ayni hash/dogrulama katmanina bagli. Hashleme/dogrulama katmani bozuldugunda mevcut hesabin parolasi dogru olsa bile backend `Invalid email or password` donebiliyor.

3. Google OAuth endpoint'i, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` veya `GOOGLE_REDIRECT_URI` canli ortam ayarlari eksik/uyumsuz oldugunda URL uretemiyor. Bu yuzden Google hesap secim penceresi yerine backend JSON/500 hata sayfasi aciliyor.

4. Canli backend `APP_ENV=development` olarak calisiyor. Bu tek basina auth hatasinin kok nedeni degil, fakat canli ortam degiskenlerinin eksik ya da tam uygulanmadigini gosteriyor.

## Yapilan Kod Degisiklikleri

- `backendWindsurf2/requirements.txt`
  - `bcrypt==4.0.1` eklendi.
  - Amac: `passlib==1.7.4` ile uyumlu, bilinen calisan bcrypt backend'ini deployda sabitlemek.

- `backendWindsurf2/services/auth_service.py`
  - Google OAuth query string uretimi manuel string birlestirme yerine `urllib.parse.urlencode` ile yapildi.
  - Amac: `redirect_uri` ve scope gibi parametrelerin URL icinde guvenli kodlanmasi.

- `backendWindsurf2/.env.production.example`
  - Canli frontend/backend adresleri ornek production degerlerine guncellendi.

## Canliya Uygulama Adimlari

Backend tekrar deploy edilmelidir:

```bash
cd backendWindsurf2
fly deploy
```

Fly secrets tarafinda su degerler tanimli olmalidir:

```bash
fly secrets set APP_ENV=production
fly secrets set DEBUG=false
fly secrets set FRONTEND_URL=https://exam-ai-xi.vercel.app
fly secrets set ALLOWED_ORIGINS=https://exam-ai-xi.vercel.app
fly secrets set ALLOWED_HOSTS=backendwindsurf2.fly.dev
fly secrets set GOOGLE_REDIRECT_URI=https://backendwindsurf2.fly.dev/api/v1/auth/google/callback
fly secrets set GOOGLE_CLIENT_ID=...
fly secrets set GOOGLE_CLIENT_SECRET=...
```

Google Cloud Console tarafinda OAuth Client ayarlarinda su redirect URI ekli olmalidir:

```text
https://backendwindsurf2.fly.dev/api/v1/auth/google/callback
```

Frontend tarafinda Vercel environment variable:

```text
VITE_API_URL=https://backendwindsurf2.fly.dev
```

## Deploy Sonrasi Kontrol

1. `https://backendwindsurf2.fly.dev/health` cevabinda `environment` degeri `production` olmali.
2. Yeni kullanici kaydi `Failed to hash password` vermemeli.
3. Mevcut kullanici login denemesi dogru parola ile token dondurmeli.
4. `https://backendwindsurf2.fly.dev/api/v1/auth/google` Google hesap secim/izin ekranina redirect etmeli.

