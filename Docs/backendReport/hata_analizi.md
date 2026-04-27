# ExamAI Backend – Hata Analizi ve Düzeltme Raporu

> **Kapsam:** `backendWindsurf2/` klasörü · **Tarih:** 2026-03-26  15.34
> **Kaynak:** `BACKEND_HATA_ANALIZI.md` ve tüm kaynak dosyaların manuel incelemesi

---

## 1. Mevcut Durumun Özeti

`backendWindsurf2` klasörü, `BACKEND_HATA_ANALIZI.md`'de listelenen pek çok sorunu **zaten düzeltmiş** durumda:

| Önceki analiz maddesi | Durum (backendWindsurf2'de) |
|---|---|
| Google OAuth callback'te try-catch yok | ✅ Düzeltilmiş → try-except eklenmiş |
| Note content kontrolü eksik | ✅ Düzeltilmiş → şifreli metin uzunluğu kontrol ediliyor |
| DB bağlantı havuzu sabit kodlanmış | ✅ Düzeltilmiş → env variable ile konfigüre ediliyor |
| Veritabanı indeksleri eksik | ✅ Düzeltilmiş → `Index(...)` tanımları tüm modellere eklendi |
| Logging yapılandırması eksik | ✅ Düzeltilmiş → JSON & dev formatı ile `utils/logger.py` hazır |
| Note şifreleme implementasyonu eksik | ✅ Düzeltilmiş → AES-256-GCM tam olarak implement edilmiş |
| Alembic migration dosyaları yok | ✅ Düzeltilmiş → `alembic/` klasörü mevcut |

---

## 2. Tespit Edilen ve Düzeltilen Hatalar

### 🔴 HATA-01 — Güvensiz Şifreleme Fallback'i

**Dosya:** `utils/security.py` · `_get_key()` fonksiyonu  
**Ciddiyet:** KRİTİK

**Sorun:**  
`NOTE_ENCRYPTION_KEY` ayarlanmamışsa veya geçersizse, fonksiyon sessizce `b"\x00" * 32` (32 sıfır byte) anahtarını kullanıyordu. Bu, tüm kullanıcı notlarının trivial (bilinen) bir anahtarla "şifrelenmiş" gibi görünmesine ama aslında tamamen güvensiz olmasına yol açar. Hata sessiz olduğu için production ortamında keşfedilmesi çok güç.

**Önceki kod:**
```python
def _get_key() -> bytes:
    try:
        raw = settings.NOTE_ENCRYPTION_KEY
        if not raw:
            return b"\x00" * 32  # ← Sessiz ve tehlikeli fallback
        ...
    except Exception as e:
        return b"\x00" * 32      # ← Her hatada aynı tehlikeli fallback
```

**Yapılan düzeltme:**  
Fallback tamamen kaldırıldı. Anahtar eksik veya placeholder değerindeyse `RuntimeError` fırlatılarak uygulama başlamadan uyarı verir.

```python
def _get_key() -> bytes:
    raw = settings.NOTE_ENCRYPTION_KEY
    if not raw or raw.startswith("changeme"):
        raise RuntimeError(
            "NOTE_ENCRYPTION_KEY is not set or is using the placeholder value. ..."
        )
    key = base64.b64decode(raw)
    if len(key) != 32:
        raise RuntimeError(...)
    return key
```

**Anahtar üretme komutu:**
```bash
python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

---

### 🔴 HATA-02 — TrustedHostMiddleware Wildcard Kullanımı

**Dosya:** `main.py` · satır 72  
**Ciddiyet:** KRİTİK

**Sorun:**  
`TrustedHostMiddleware` yalnızca production'da etkinleştiriliyor, ancak `allowed_hosts=["*"]` olarak ayarlı — yani middleware aktif ama her host'a izin veriyor. Bu, Host Header Injection saldırılarına tam anlamıyla kapı açar.

**Önceki kod:**
```python
if settings.is_production:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])  # ← İşlevsiz
```

**Yapılan düzeltme:**  
`config.py`'ye yeni `ALLOWED_HOSTS` alanı ve `allowed_hosts` property'si eklendi. `main.py` bu değeri kullanıyor.

```python
# config.py (eklendi)
ALLOWED_HOSTS: str = "localhost"

@property
def allowed_hosts(self) -> list[str]:
    return [h.strip() for h in self.ALLOWED_HOSTS.split(",")]

# main.py (düzeltildi)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
```

**Gerekli `.env` değişkeni:**
```
ALLOWED_HOSTS=examai.com,api.examai.com
```

---

### 🔴 HATA-03 — Redis Cache Temizleme Fonksiyonu Çalışmıyordu

**Dosya:** `services/cache_service.py` · `clear_user_cache()` ve `set_cached_quiz()`  
**Ciddiyet:** YÜKSEK (Fonksiyonel hata)

**Sorun:**  
Cache anahtarları `SHA-256` hash'i ile oluşturuluyor: `quiz:cache:<sha256_digest>`. `clear_user_cache()` ise tüm `quiz:cache:*` anahtarlarını çekip içinde `user_id` arayıyordu — ama `user_id` hash içinde artık görünmüyor. Sonuç: **fonksiyon hiçbir zaman hiçbir şey silmiyordu.**

Ayrıca production ortamında `redis.keys("quiz:cache:*")` çağrısı tüm Redis'i tarıyan engelleyici bir işlemdir; büyük veri setlerinde ciddi performans sorunu yaratır.

**Önceki kod:**
```python
# keys = tüm hash'ler; user_id hiçbirinin içinde yok
user_keys = [key for key in keys if user_id in key]  # ← Her zaman boş liste!
```

**Yapılan düzeltme:**  
`set_cached_quiz()` her kayıt sırasında bir Redis Set'e (`quiz:user_keys:<user_id>`) cache anahtarını ekliyor. `clear_user_cache()` bu set'i okuyarak doğrudan ilgili anahtarları siliyor.

```python
# set_cached_quiz (eklendi)
user_set_key = f"quiz:user_keys:{user_id}"
await redis.sadd(user_set_key, key)
await redis.expire(user_set_key, ttl_seconds)

# clear_user_cache (düzeltildi)
user_set_key = f"quiz:user_keys:{user_id}"
keys = await redis.smembers(user_set_key)  # O(1) kullanıcı başı lookup
if keys:
    await redis.delete(*keys)
    await redis.delete(user_set_key)
```

---

### 🟡 HATA-04 — Google OAuth: Pasif Kullanıcı Girişi Engellenmiyor

**Dosya:** `services/auth_service.py` · `google_login_or_create()`  
**Ciddiyet:** ORTA

**Sorun:**  
E-posta/parola ile giriş yapan `get_current_user` ve `authenticate_user` fonksiyonları `is_active` kontrolü yapıyor. Ancak Google OAuth ile giriş yapan mevcut kullanıcılar için bu kontrol yapılmıyordu. Pasife alınan bir hesap Google ile giriş yapmaya devam edebiliyordu.

**Yapılan düzeltme:**
```python
else:
    if not user.is_active:
        logger.warning(f"Inactive user attempted Google OAuth login: {email}")
        raise ValueError("User account is inactive.")
    logger.info(f"Existing user logged in via Google OAuth: {email}")
```

---

### 🟡 HATA-05 — Gemini API Token Limiti Çok Düşük

**Dosya:** `services/ai_service.py` · `_call_gemini_api()`  
**Ciddiyet:** ORTA (Fonksiyonel eksiklik)

**Sorun:**  
`maxOutputTokens: 2048` ile 10+ soruluk quizler için yeterli alan yok. Gemini yanıtı kesilebiliyor ve JSON parse hatası oluşabiliyor. Ayrıca `responseMimeType` belirtilmediği için model zaman zaman JSON yerine Markdown veya açıklamalı metin döndürebiliyordu, bu da kırılgan regex fallback'ini tetikliyordu.

**Yapılan düzeltme:**
```python
"generationConfig": {
    "temperature": 0.7,
    "maxOutputTokens": 8192,           # 2048 → 8192
    "responseMimeType": "application/json",  # Yapılandırılmış JSON zorunlu
}
```

---

### 🟢 HATA-06 — Deprecated `datetime.utcnow()` Kullanımı

**Dosya:** `utils/logger.py`  
**Ciddiyet:** DÜŞÜK (Gelecek Python sürümlerinde kırılacak)

**Sorun:**  
`datetime.utcnow()` Python 3.12'de `DeprecationWarning` veriyor ve gelecek sürümlerde kaldırılacak. Timezone-naive datetime döndürdüğü için ISO 8601 log timestamp'leri UTC offset içermiyor (`2026-01-01T10:00:00` yerine `2026-01-01T10:00:00+00:00` olmalı).

**Yapılan düzeltme:**
```python
# Öncesi
from datetime import datetime
log_record['timestamp'] = datetime.utcnow().isoformat()

# Sonrası
from datetime import datetime, timezone
log_record['timestamp'] = datetime.now(timezone.utc).isoformat()
```

---

## 3. Konfigürasyon Gereksinimleri (Değiştirilmemiş)

Aşağıdaki maddeler **kod hatası değil**, production deployment öncesi yapılması gereken konfigürasyon işlemleridir. Kod düzeltmesi gerektirmiyor, sadece gerçek değerlerin `.env` dosyasına girilmesi yeterli:

| Madde | Yapılacak İşlem |
|---|---|
| `SECRET_KEY` | `openssl rand -hex 32` ile üret |
| `NOTE_ENCRYPTION_KEY` | Yukarıdaki Python komutuyla üret |
| `GOOGLE_CLIENT_ID / SECRET` | Google Cloud Console'dan al |
| `GEMINI_API_KEY` | Google AI Studio'dan al |
| `DATABASE_URL` | Güçlü parola ile production DB URL'si |
| `ALLOWED_HOSTS` | Gerçek domain adları (örn. `examai.com`) |
| `ALLOWED_ORIGINS` | Frontend URL'leri (örn. `https://examai.com`) |

---

## 4. Bilinen Eksiklikler (Kapsam Dışı / İleride Yapılacaklar)

Bu rapor kapsamında **kod düzeltmesi yapılmamıştır**, ancak aşağıdaki eksiklikler de mevcuttur:

- **Rate Limiting:** API endpoint'lerinde `slowapi` veya benzeri bir kütüphane ile rate limiting eklenmeli.
- **Test Dosyaları:** `tests/` klasörü boş. Pytest ile unit ve integration testleri yazılmalı.
- **Audit Loglama:** Kullanıcı işlemleri (giriş, quiz oluşturma, not silme) için audit log mekanizması yok.
- **Celery Monitoring:** Flower veya benzeri bir araç ile background task monitörü kurulmalı.
- **N+1 Sorgu Problemi:** Quiz → Question ilişkilerinde `selectinload` kullanılarak eager loading eklenmeli.
- **Data Anonymization:** Gemini API'ye gönderilen note içeriklerinde PII maskeleme yapılmıyor.
- **Alembic Migration:** `alembic/` klasörü mevcut, ancak `alembic revision --autogenerate` ile ilk migration oluşturulmalı.

---

## 5. Düzeltme Özeti

| # | Dosya | Hata | Düzeltme |
|---|---|---|---|
| 1 | `utils/security.py` | Sessiz sıfır anahtar fallback (KRİTİK) | `RuntimeError` fırlatacak şekilde değiştirildi |
| 2 | `main.py` | TrustedHostMiddleware wildcard `["*"]` | `settings.allowed_hosts` ile değiştirildi |
| 3 | `config.py` | `ALLOWED_HOSTS` alanı eksikti | Yeni alan + property eklendi |
| 4 | `services/cache_service.py` | `clear_user_cache` hiç çalışmıyordu | Redis Set tabanlı tracking ile yeniden yazıldı |
| 5 | `services/auth_service.py` | Google OAuth'ta `is_active` kontrolü yok | Mevcut kullanıcı dalına kontrol eklendi |
| 6 | `services/ai_service.py` | Token limiti çok düşük, JSON formatı garantisiz | `maxOutputTokens` artırıldı + `responseMimeType` eklendi |
| 7 | `utils/logger.py` | Deprecated `datetime.utcnow()` | Timezone-aware `datetime.now(timezone.utc)` ile değiştirildi |
