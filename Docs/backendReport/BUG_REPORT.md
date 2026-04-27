# ExamAI Backend — Hata Analiz Raporu

**Tarih:** 2026-03-25 | **Analiz Edilen Versiyon:** 1.0.0 | **Toplam Hata:** 6

---

## Özet

| # | Dosya | Hata Türü | Önem |
|---|---|---|---|
| 1 | `routers/auth.py` | `/auth/me` her zaman 501 fırlatıyor | 🔴 Kritik |
| 2 | `services/quiz_service.py` | UUID ↔ str tip uyumsuzluğu (`_get_weak_topics`) | 🔴 Kritik |
| 3 | `services/quiz_service.py` | `time.sleep()` async context'i bloke ediyor | 🟠 Yüksek |
| 4 | `services/quiz_service.py` | `parsed` değişkeni `UnboundLocalError` riski | 🟠 Yüksek |
| 5 | `services/grading_service.py` | `time.sleep()` async context'i bloke ediyor | 🟠 Yüksek |
| 6 | `routers/quiz.py` + `routers/answers.py` | Çift/tutarsız cache key + N+1 sorgu | 🟡 Orta |

---

## Hata Detayları

---

### Hata #1 — `/auth/me` Endpoint'i Hiç Çalışmıyor

**Dosya:** [`routers/auth.py`](file:///c:/Users/ozgur/Desktop/EXAM_AI/backend/routers/auth.py)  
**Önem:** 🔴 Kritik  
**Tür:** Mantık Hatası

**Açıklama:**  
`/api/v1/auth/me` endpoint'i her koşulda `HTTP 501 Not Implemented` fırlatıyordu. Kullanıcı kimlik doğrulaması için temel olan bu endpoint hiçbir zaman kullanıcı dönmüyordu.

**Hatalı Kod:**
```python
@router.get("/me", response_model=UserRead)
async def me(db: AsyncSession = Depends(get_db)):
    from services.auth_service import get_current_user
    from fastapi import Depends as _Depends
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Use bearer token...")
```

**Düzeltilmiş Kod:**
```python
@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)):
    """Returns the current authenticated user's profile (Bearer token required)."""
    return current_user
```

---

### Hata #2 — UUID / String Tip Uyumsuzluğu (`_get_weak_topics`)

**Dosya:** [`services/quiz_service.py`](file:///c:/Users/ozgur/Desktop/EXAM_AI/backend/services/quiz_service.py)  
**Önem:** 🔴 Kritik  
**Tür:** Tip Hatası (Runtime)

**Açıklama:**  
`_get_weak_topics()` fonksiyonu `user_id` parametresini `str` olarak alıp doğrudan `Answer.user_id == user_id` karşılaştırmasında kullanıyordu. Ancak `Answer.user_id` PostgreSQL'de `UUID` tipinde. Bu durum sorgunun sonuç dönmemesine (sessiz başarısızlık) veya veritabanı hatasına yol açar. Ayrıca `ans.question.topic` erişimi `joinedload` olmadan N+1 lazy-load tetikler.

**Hatalı Kod:**
```python
async def _get_weak_topics(db: AsyncSession, user_id: str) -> list[str]:
    result = await db.execute(
        select(Answer).where(Answer.user_id == user_id, ...)  # str vs UUID!
    )
    answers = result.scalars().all()
    for ans in answers:
        topic = ans.question.topic  # N+1 lazy-load
```

**Düzeltilmiş Kod:**
```python
async def _get_weak_topics(db: AsyncSession, user_id: str) -> list[str]:
    from sqlalchemy.orm import joinedload
    uid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
    result = await db.execute(
        select(Answer)
        .options(joinedload(Answer.question))   # N+1 giderildi
        .where(Answer.user_id == uid, ...)      # UUID karşılaştırması
    )
```

---

### Hata #3 — `time.sleep()` Async Context'i Bloke Ediyor (quiz_service)

**Dosya:** [`services/quiz_service.py`](file:///c:/Users/ozgur/Desktop/EXAM_AI/backend/services/quiz_service.py)  
**Önem:** 🟠 Yüksek  
**Tür:** Performans / Concurrency Hatası

**Açıklama:**  
Gemini API yeniden deneme (retry) döngüsünde `time.sleep()` kullanılıyordu. Bu, `async` bir fonksiyon içinde tüm event loop'u dondurur; diğer async görevlerin çalışmasını engeller.

**Hatalı Kod:**
```python
import time
# ...
time.sleep(wait)   # Event loop'u bloke eder!
```

**Düzeltilmiş Kod:**
```python
import asyncio
# ...
await asyncio.sleep(wait)   # Non-blocking, event loop serbest kalır
```

---

### Hata #4 — `parsed` Değişkeni Tanımsız Kalabilir (`UnboundLocalError`)

**Dosya:** [`services/quiz_service.py`](file:///c:/Users/ozgur/Desktop/EXAM_AI/backend/services/quiz_service.py)  
**Önem:** 🟠 Yüksek  
**Tür:** Mantık Hatası (Runtime Crash)

**Açıklama:**  
3'lü retry döngüsünde tüm denemeler farklı exception türleri fırlatıp başarısız olursa (örn. `json.JSONDecodeError` değil başka bir exception), `parsed` değişkeni hiç atanmadan döngü biter ve sonrasındaki `parsed.test_sorulari` satırı `UnboundLocalError` verir.

**Hatalı Kod:**
```python
for attempt in range(3):
    try:
        ...
        parsed = validate_quiz_output(raw_json)
        break
    except (json.JSONDecodeError, ValueError):
        ...

# parsed burada tanımsız olabilir!
for idx, q in enumerate(parsed.test_sorulari):
```

**Düzeltilmiş Kod:**
```python
parsed = None                          # Başlangıç değeri
for attempt in range(3):
    ...
if parsed is None:                     # Tüm retry'lar başarısız
    raise ValueError("Quiz generation failed: no valid output from Gemini.")
```

---

### Hata #5 — `time.sleep()` Async Context'i Bloke Ediyor (grading_service)

**Dosya:** [`services/grading_service.py`](file:///c:/Users/ozgur/Desktop/EXAM_AI/backend/services/grading_service.py)  
**Önem:** 🟠 Yüksek  
**Tür:** Performans / Concurrency Hatası

**Açıklama:**  
Hata #3 ile aynı sorun; `grade_open_ended()` fonksiyonunun retry döngüsünde de `time.sleep()` kullanılıyordu.

**Hatalı Kod:**
```python
import time
# ...
time.sleep(2 ** attempt)
```

**Düzeltilmiş Kod:**
```python
import asyncio
# ...
await asyncio.sleep(2 ** attempt)
```

---

### Hata #6 — Tutarsız Cache Key + N+1 Sorgusu

**Dosyalar:** [`routers/quiz.py`](file:///c:/Users/ozgur/Desktop/EXAM_AI/backend/routers/quiz.py), [`routers/answers.py`](file:///c:/Users/ozgur/Desktop/EXAM_AI/backend/routers/answers.py)  
**Önem:** 🟡 Orta  
**Tür:** Mantık Hatası + Performans Hatası

**Açıklama (6a — Tutarsız Cache Key):**  
`quiz.py` router'ı cache key'i `sha256(f"{user_id}{note_id}...")` formatıyla hesaplıyordu. Ancak `cache_service._build_cache_key()` farklı bir format (`f"{user_id}:{note_id}:..."` — aralarında `:` var) kullanıyor. Sonuç olarak router'ın hesapladığı `cache_key` DB sütununa yazılıyor ama Redis'teki gerçek key'le hiç eşleşmiyordu.

**Düzeltilmiş Kod:**
```python
# cache_service'deki canonical fonksiyon kullanılıyor
from services.cache_service import _build_cache_key
cache_key = _build_cache_key(uid, nid, body.total_questions, body.mc_ratio, body.difficulty)
```

**Açıklama (6b — N+1 Sorgu):**  
`answers.py`'de her cevap için ayrı `db.get(Question, sub.question_id)` çağrısı yapılıyordu. 10 sorulu bir sınavda 10 ayrı DB sorgusu anlamına gelir.

**Düzeltilmiş Kod:**
```python
# Tüm sorular tek sorguda çekildi, dict'e aktarıldı
q_result = await db.execute(select(Question).where(Question.quiz_id == quiz_id))
questions_map = {q.id: q for q in q_result.scalars().all()}
# Döngüde: question = questions_map.get(sub.question_id)
```

---

## ExamAI.md Gereksinim Karşılama Durumu (Hata Sonrası)

| İş Paketi | Gereksinim | Durum |
|---|---|---|
| İP1 | FastAPI + .env + JWT + Google OAuth | ✅ |
| İP1 | DB modelleri (User, Note, Quiz, Question, Answer) | ✅ |
| İP1 | Not şifreleme (AES-256-GCM) | ✅ |
| İP2 | OpenCV görsel ön-işleme | ✅ |
| İP2 | Tesseract + Gemini OCR stratejisi | ✅ |
| İP2 | Düşük kalite uyarısı | ✅ |
| İP3 | Kişiselleştirilmiş prompt (zayıf konular) | ✅ (Hata #2 düzeltildi) |
| İP3 | Token optimizasyonu (özetleme + batch) | ✅ |
| İP3 | Redis önbellekleme | ✅ (Hata #6a düzeltildi) |
| İP3 | Celery async + durum bildirimi | ✅ |
| İP3 | Exponential backoff | ✅ (Hata #3, #4, #5 düzeltildi) |
| İP4 | MC backend puanlama (AI kullanılmaz) | ✅ |
| İP4 | Açık uçlu Gemini puanlama | ✅ |
| İP4 | Konu etiketleme (`Question.topic`) | ✅ |
| İP4 | Analitik rapor + zayıf konu önerileri | ✅ |
| İP5 | Swagger dokümantasyonu | ✅ |
| İP5 | Pydantic şema validasyonu | ✅ |

---

*Rapor otomatik olarak kod analizi sırasında üretilmiştir.*
