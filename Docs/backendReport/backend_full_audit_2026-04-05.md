# ExamAI Backend – Kapsamlı Analiz Raporu
**Tarih:** 2026-04-05  
**Analiz Edilen Dizin:** `backendWindsurf2/`  
**Durum:** Kritik + Orta + Düşük Öncelikli Bulgular

---

## 1. Özet (Executive Summary)

Backend FastAPI mimarisi genel olarak sağlam tasarlanmış; async SQLAlchemy, Pydantic v2, Celery + Redis, JWT auth ve AES-256-GCM şifreleme doğru seçilmiş araçlardır.  
Ancak aşağıda detaylandırılan **5 kritik**, **8 orta** ve **4 düşük** öncelikli sorun tespit edilmiştir.

---

## 2. KRİTİK SORUNLAR 🔴

---

### KRTK-1 — Alembic Versions Klasörü Boş, Hayalet Revizyon Referansı

**Dosya:** `alembic/versions/` (boş)  
**Hata:**
```
ERROR: Can't locate revision identified by 'aaa774a83dda'
FAILED: Can't locate revision identified by 'aaa774a83dda'
```

**Kök Neden:**  
PostgreSQL'deki `alembic_version` tablosunda `aaa774a83dda` revizyon ID'si hâlâ kayıtlı, ancak bu revizyona karşılık gelen `.py` dosyası `alembic/versions/` klasöründe **mevcut değil**. Dosya silinmiş ya da hiç commit'enmemiş.

**Çözüm (Adım Adım):**

**Yöntem A – Veritabanı temiz slate (Tavsiye Edilen):**
```powershell
# 1. alembic_version tablosunu sıfırla
# psql veya pgAdmin'de çalıştır:
#    DELETE FROM alembic_version;

# 2. versions/ klasöründeki tüm .py dosyalarını sil (zaten boş)

# 3. Yeni initial migration oluştur
cd C:\Users\ozgur\Desktop\EXAM_AI\backendWindsurf2
.venv\Scripts\activate
alembic revision --autogenerate -m "Initial migration"

# 4. Migration'ı uygula
alembic upgrade head
```

**Yöntem B – Sahte revision ile köprüle (DB'yi silmek istemiyorsan):**
```powershell
# Eksik revision'ı boş bir dosya olarak oluştur
alembic revision --rev-id aaa774a83dda -m "placeholder"
# Oluşturulan dosyayı aç, upgrade/downgrade fonksiyonlarını boş bırak
# Sonra:
alembic upgrade head
```

> **NOT:** Eğer veritabanında henüz gerçek veri yoksa Yöntem A her zaman tercih edilmelidir.

---

### KRTK-2 — Güvensiz SECRET_KEY Varsayılan Değeri

**Dosya:** `.env` satır 7, `config.py` satır 19  
```python
SECRET_KEY: str = "changeme-use-openssl-rand-hex-32"
```
```env
SECRET_KEY=changeme-use-openssl-rand-hex-32
```

**Risk:** JWT token'ları kolayca taklit edilebilir; kimlik doğrulama tamamen devre dışı kalır.

**Çözüm:**
```powershell
# PowerShell'de güvenli anahtar üret
python -c "import secrets; print(secrets.token_hex(32))"
# Üretilen değeri .env dosyasına yaz
SECRET_KEY=<üretilen_değer>
```

---

### KRTK-3 — API Anahtarları .env'de Açık Metin (Güvenlik Açığı)

**Dosya:** `.env`
```env
GOOGLE_CLIENT_SECRET=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
GEMINI_API_KEY=AIzaSyBx9QBo_fhyBk6UJDYgpdpSNvlFuMOAJjw
GOOGLE_CLIENT_ID=292215527768-...
NOTE_ENCRYPTION_KEY=M/nUfv6PgBJOg0zbd+1T6lcp9ewbWOWIlDzuaBKTVqk=
```

**Risk:** `.env` git'e giderse tüm anahtarlar sızdırılır. Google/Gemini API anahtarları bu raporda görünmektedir.

**Çözüm:**
1. `.gitignore`'a `.env` ekleyin (kontrol edin)
2. Mümkünse bu anahtarları Google Cloud Console'dan iptal edip yenileyin
3. `.env.example` dosyasını kullanın (var, doğru yaklaşım)

---

### KRTK-4 — `celery_tasks.py` İçinde `clean_text` İmport Edilmiyor

**Dosya:** `services/celery_tasks.py` satır 169  
```python
cleaned_text = clean_text(raw_text)  # NameError: name 'clean_text' is not defined
```

**Sorun:** `process_note_task` fonksiyonu içinde `clean_text` çağrılıyor ancak bu modülde import edilmemiş. En üste `from services.extraction_service import clean_text` satırı yoktur.

**Küçük not:** Aynı dosyada kendi `clean_text` tanımı (satır 195) da var, ama `_process_note` async closure'u onu görmüyor çünkü closure tanımında yerel scope'da çözümleme yapılıyor ve `asyncio.run()` içinde çağrıldığında farklı bir thread context'i oluşabilir. Güvenli yaklaşım: modül seviyesi import kullanın.

**Çözüm:**
```python
# celery_tasks.py en üstüne ekle:
from services.extraction_service import clean_text as _clean_note_text

# process_note_task içinde değiştir:
cleaned_text = _clean_note_text(raw_text)
```

---

### KRTK-5 — `notes.py` Router'ı Şifreleme Yapmadan Ham Metin Kaydediyor

**Dosya:** `routers/notes.py` satır 196-199  
```python
# Model encrypted alanlar kullanıyor; ham metni direkt store ediyoruz.
raw_text_encrypted=raw_text,
cleaned_text_encrypted=cleaned_text,
```

**Sorun:** Model sütunları `_encrypted` suffix'i taşıyor ve DB şeması AES-256-GCM şifreli veri bekliyor. Ancak router şifreleme **yapmıyor**. Sonra `quiz.py`'de `decrypt_text()` çağrılıyor:
```python
cleaned_text = decrypt_text(note.cleaned_text_encrypted)  # BOZUK VERİ: şifresiz metin
```
Bu her quiz oluşturma denemesinde `ValueError: Failed to decrypt text` üretir.

**Çözüm:**
```python
# routers/notes.py içine import ekle:
from utils.security import encrypt_text

# Note oluştururken:
note = Note(
    ...
    raw_text_encrypted=encrypt_text(raw_text),
    cleaned_text_encrypted=encrypt_text(cleaned_text),
)
```

---

## 3. ORTA ÖNCELİKLİ SORUNLAR 🟡

---

### ORTA-1 — `register_user` Çift `commit` Çağrısı (Çift Kayıt Riski)

**Dosya:** `services/auth_service.py` satır 41-43
```python
db.add(user)
await db.commit()    # auth_service içinde commit
await db.refresh(user)
```
`get_db` dependency'si zaten her request sonunda `commit()` yapıyor (`database.py` satır 39). Bu çift commit, transaction bütünlüğünü bozabilir ve race condition'a yol açabilir.

**Çözüm:** `auth_service.py`'den `await db.commit()` ve `await db.rollback()` çıkarın; sadece `db.add(user)` ve `await db.flush()` kullanın.

---

### ORTA-2 — `auth_service.py` Google OAuth Kullanıcısı İçin `hashed_password=""`

**Dosya:** `services/auth_service.py` satır 196
```python
hashed_password="",  # No password for OAuth users
```

**Sorun:** Empty string bcrypt hash'i değil. Eğer kullanıcı şifreyle login dener ve `verify_password("", "")` çağrılırsa beklenmedik davranış ortaya çıkabilir. Ayrıca `NULL` yerine boş string kullanmak DB kısıtlamalarıyla çelişebilir.

**Çözüm:**
```python
hashed_password=None,  # OAuth kullanıcıları için NULL
```

---

### ORTA-3 — `ocr_service.py` CRLF Satır Sonları (Windows → Unix Uyumsuzluğu)

**Dosya:** `services/ocr_service.py`  
Tüm dosya `\r\n` satır sonlarına sahip. Docker/Linux ortamında çalıştırıldığında Python içindeki string literal'lar ve `re` pattern'leri etkilenebilir.

**Çözüm:** Dosyayı LF olarak kaydedin:
```powershell
(Get-Content .\services\ocr_service.py -Raw).Replace("`r`n", "`n") | Set-Content .\services\ocr_service.py -NoNewline
```

---

### ORTA-4 — `quiz.py` Router'da `flush()` Sonrası Celery Görevi Başlatılıyor, `commit()` Öncesi

**Dosya:** `routers/quiz.py` satır 101-108  
```python
await db.flush()   # ID üretildi ama DB'ye yazılmadı
...
generate_quiz_task.delay(str(quiz.id), cleaned_text)  # Celery gözü kapalı çalışıyor
```

**Sorun:** Celery task PostgreSQL'deki quiz kaydını `quiz_id` ile bulmaya çalıştığında kayıt henüz `commit` edilmemiş olabilir → `Quiz not found` hatası.

**Çözüm:** Celery task'ı `commit()`'ten **sonra** çağırın:
```python
await db.flush()
cache_key = _build_cache_key(...)
quiz = Quiz(...)
db.add(quiz)
await db.flush()
await db.commit()  # Önce commit
generate_quiz_task.delay(...)  # Sonra Celery
```

---

### ORTA-5 — `celery_tasks.py`'de `asyncio.run()` Celery Worker'da Sorun Çıkarabilir

**Dosya:** `services/celery_tasks.py` satır 129, 192, 348  
```python
return asyncio.run(_generate_quiz())
```

**Sorun:** Bazı Celery worker konfigürasyonlarında (özellikle `gevent` veya `eventlet` pool ile) `asyncio.run()` çakışabilir. Windows'ta `asyncio` loop'ların yeniden kullanımı farklı davranır.

**Çözüm:** Celery için sync database driver kullanın (`psycopg2` tabanlı) veya `nest_asyncio` ile sarın:
```python
import nest_asyncio
nest_asyncio.apply()
```

---

### ORTA-6 — `requirements.txt`'de Sürüm Çakışması Riski (FastAPI 0.104.1 + SQLAlchemy 2.0.23)

`fastapi==0.104.1` oldukça eski. SQLAlchemy 2.0.23 ve Pydantic 2.5.0 ile uyum sorunu yaşanabilir. En az `fastapi>=0.110.0` önerilir.

---

### ORTA-7 — `alembic.ini` ve `env.py` İçindeki Hardcoded DB URL Çakışması

**Dosya:** `alembic.ini` satır 75
```ini
sqlalchemy.url = postgresql+asyncpg://examai_user:password@localhost:5432/examai_db
```

**Sorun:** `env.py` bu değeri `settings.DATABASE_URL` ile override ediyor (`get_url()` fonksiyonu). Ancak `.ini` içindeki hardcoded URL yanlış credentials içeriyorsa offline mode'da sorun yaratır.

**Çözüm:** `alembic.ini`'den `sqlalchemy.url` satırını kaldırın; sadece `env.py`'deki `get_url()` kullanılsın.

---

### ORTA-8 — `note.py` Modelinde `context_id` `unique=True` Ama `default=lambda`

**Dosya:** `models/note.py` satır 20
```python
context_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, default=lambda: str(uuid.uuid4()))
```

**Sorun:** `uuid4()` çakışma ihtimali teorik olarak var (çok nadiren). Daha önemlisi, bu lambda SQLAlchemy ORM layer'ında çalışır ve migration sırasında `server_default` değil `python-side default` olarak kalır. Şema düzeyinde next sequence veya `gen_random_uuid()` tercih edilebilir.

---

## 4. DÜŞÜK ÖNCELİKLİ SORUNLAR / İYİLEŞTİRMELER 🔵

---

### DÜŞ-1 — `main.py`'de `init_db()` Migration'ı Bypass Ediyor

**Dosya:** `main.py` satır 30
```python
await init_db()  # Base.metadata.create_all() çağırır
```

**Sorun:** Bu, Alembic migration'larını bypass eder. Production'da tabloların Alembic ile yönetilmesi gerekir. `create_all` sadece geliştirme ortamında kabul edilebilir.

**Çözüm:**
```python
if settings.DEBUG:
    await init_db()
else:
    logger.info("Production: skipping create_all, use Alembic migrations")
```

---

### DÜŞ-2 — Google OAuth URL Oluşturma Güvenli Değil (State Parametresi Eksik)

**Dosya:** `services/auth_service.py` satır 122-132  
OAuth 2.0 spesifikasyonuna göre CSRF koruması için `state` parametresi zorunludur. Mevcut implementasyon `state` göndermemektedir.

```python
params = {
    ...
    "state": secrets.token_urlsafe(32),  # CSRF token
}
# State'i Redis/session'a kaydet ve callback'te doğrula
```

---

### DÜŞ-3 — `schemas/quiz.py`'de `QuizGradingResponse.grading_results` İçin Tip Uyumsuzluğu

**Dosya:** `routers/quiz.py` satır 366-373
```python
grading_results.append({
    "question_id": answer.question_id,  # UUID objesi
    "score": answer.score or 0,
    ...
})
```

`GradingResult.score` tipi `int` olarak tanımlı; `answer.score` ise `int | None`. `or 0` kurtarıyor ama explicit cast daha güvenlidir.

---

### DÜŞ-4 — `celery_tasks.py` İçinde `grade_quiz_task` Sürekli Her Sorudan Sonra `commit()`

**Dosya:** `services/celery_tasks.py` satır 322
```python
grading.graded_questions = graded_count
await db.commit()  # Her soru için commit!
```

Yüksek soru sayısında (50 soru) bu 50 ayrı commit anlamına gelir. Daha iyi yaklaşım: batch update veya döngü bitince tek commit.

---

## 5. MİMARİ DEĞERLENDİRME

| Bileşen | Durum | Not |
|---------|-------|-----|
| FastAPI Router Yapısı | ✅ İyi | Prefix, tags, error handling doğru |
| SQLAlchemy ORM Modelleri | ✅ İyi | UUID PK, ilişkiler, indeksler doğru |
| Pydantic Schemas | ✅ İyi | `from_attributes`, field validation doğru |
| JWT Authentication | ⚠️ Orta | SECRET_KEY güvensiz (KRTK-2) |
| AES-256-GCM Şifreleme | ⚠️ Orta | Mekanizma doğru, kullanım hatalı (KRTK-5) |
| Alembic Migration | ❌ Kritik | Hayalet revizyon, sıfırdan başlamalı (KRTK-1) |
| Celery Task Queue | ⚠️ Orta | asyncio.run() riski (ORTA-5) |
| Redis Cache | ✅ İyi | Composite key hash, TTL, user invalidation |
| OCR / Extraction Pipeline | ✅ İyi | Dual engine (fitz + tesseract), fallback |
| Error Handling | ✅ İyi | Tüm endpoint'lerde try/except + HTTP kod |
| Logging | ✅ İyi | Yapılandırılmış logger, debug/prod level |

---

## 6. ACİL EYLEM PLANI (Öncelik Sırası)

```
1. [KRTK-1] Alembic sıfırla → migration oluştur → uygula
2. [KRTK-5] routers/notes.py'de encrypt_text() kullan
3. [KRTK-2] SECRET_KEY'i güçlü bir değerle değiştir
4. [KRTK-4] celery_tasks.py'de clean_text import et
5. [ORTA-1] auth_service.py'den çift commit kaldır
6. [ORTA-4] quiz.py'de commit sonrası Celery başlat
```

---

## 7. ALEMBIC HATASI – TAM ÇÖZÜM REHBERİ

### Adım 1: Mevcut DB Revizyon Durumunu Kontrol Et
```powershell
cd C:\Users\ozgur\Desktop\EXAM_AI\backendWindsurf2
.venv\Scripts\activate
alembic current
```
Beklenen çıktı: `aaa774a83dda (head)` → Bu ID DB'de var ama dosya yok.

### Adım 2A: Veritabanında Tablolar Henüz Boş/Test Aşamasındaysa
```sql
-- pgAdmin veya psql ile çalıştır:
DELETE FROM alembic_version;
```

```powershell
# Yeni migration oluştur
alembic revision --autogenerate -m "Initial migration"
# Uygula
alembic upgrade head
```

### Adım 2B: Mevcut Veriyi Korumak İstiyorsan
```powershell
# 'aaa774a83dda' ID'siyle boş bir placeholder revision oluştur
alembic revision --rev-id aaa774a83dda -m "placeholder_existing"
```
Oluşturulan dosyayı aç (`alembic/versions/aaa774a83dda_placeholder_existing.py`) ve içini boşalt:
```python
def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
```

```powershell
# Sonra gerçek değişiklikleri ekle
alembic revision --autogenerate -m "add_notes_and_quiz_tables"
alembic upgrade head
```

### Adım 3: Doğrulama
```powershell
alembic current      # head göstermeli
alembic history      # revision zincirini göster
```

---

*Bu rapor `antigravity` tarafından otomatik olarak oluşturulmuştur.*  
*Rapor Tarihi: 2026-04-05*
