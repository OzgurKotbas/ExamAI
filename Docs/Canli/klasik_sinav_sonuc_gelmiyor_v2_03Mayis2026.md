# Klasik Sınav Sonuç Ekranına Geçilemiyor – Kök Neden Analizi ve Çözüm (03 Mayıs 2026 v2)

## Problem
Klasik sınav tamamlandıktan sonra "Cevaplarınız Değerlendiriliyor..." ekranı kaybolmuyor, sonuç ekranı gelmiyor.

---

## Tespit Edilen Kök Nedenler

### Neden 1 (Birincil – Backend): `asyncio.run()` + `uvloop` Çakışması

**Dosya:** `backendWindsurf2/services/celery_tasks.py`

`grade_quiz_task` Celery görevi, kendi içinde iç içe bir `async def _grade_quiz()` fonksiyonu tanımlıyor ve bunu `asyncio.run(_grade_quiz())` ile çalıştırıyordu:

```python
# HATALI YAPI:
def grade_quiz_task(self, ...):
    async def _grade_quiz():  # ← İç içe async fonksiyon (closure)
        ...
    return asyncio.run(_grade_quiz())  # ← SORUN BURASI
```

**Neden başarısız oluyor?**

Fly.io üretim ortamında uvicorn, `uvloop`'u event loop olarak kullanır. `nest_asyncio.apply()` uvloop'u patch edemez (bunu log satırı da doğrular: "Can't patch loop of type uvloop.Loop"). Celery worker `--pool=solo` ile çalışıyor olsa bile, `asyncio.run()` çağrısı mevcut bir event loop içinde çalıştırılmaya çalışıldığında **sessizce başarısız oluyor**.

Sonuç: Celery görevi exception fırlatıyor ama `grading.status` "failed" olarak bile güncellenemiyor. Durum sonsuza dek `"pending"` olarak kalıyor.

**Çözüm:**
`generate_quiz_task`'ın kanıtlanmış tasarımını örnek aldık: `_grade_quiz` iç fonksiyonu, `run_quiz_grading()` adlı üst-seviye bir async fonksiyona taşındı. Bu sayede `asyncio.run()` her zaman temiz bir top-level fonksiyonu çalıştırıyor.

```python
# DOĞRU YAPI:
@celery_app.task(...)
def grade_quiz_task(self, ...):
    return asyncio.run(run_quiz_grading(...))  # ← Top-level fonksiyon

async def run_quiz_grading(...):  # ← Closure değil, üst-seviye
    ...
```

---

### Neden 2 (İkincil – Frontend): Stale Closure ile `gradingId` Okunmuyor

**Dosya:** `examai-frontend/src/pages/Quiz.jsx`

`setInterval` içinde çalışan `checkGradingStatus` fonksiyonu, `gradingId` state değişkenini closure'dan okuyordu. React'ta asenkron callback'ler closure yaratıldığı andaki state değerini "kilitler". Bu yüzden `gradingId` her zaman `null` okunuyor ve hiçbir API isteği atılmıyordu.

**Çözüm:** `gradingIdRef` (`useRef`) eklendi. `gradingId` state her güncellendiğinde ref de güncellenir; interval callback ref üzerinden her zaman güncel ID'yi okur.

---

### Neden 3 (Üçüncül – Backend): AI Puanlama Sırası Yanlış

**Dosya:** `backendWindsurf2/services/ai_service.py`

`grade_open_ended_answer`, Gemini yerine Hugging Face modellerini önce deniyordu. HF'de 5+ model × 3+ token kombinasyonu denendi; her biri 150 saniye timeout ile bekledi. Bu, görevi dakikalarca bloke edebiliyordu.

**Çözüm:** `_generate_with_fallback()` fonksiyonu kullanıldı — Gemini önce, HF yedek.

---

## Değiştirilen Dosyalar

| Dosya | Değişiklik |
|-------|-----------|
| `services/celery_tasks.py` | `grade_quiz_task` → `run_quiz_grading()` top-level async fonksiyonuna taşındı |
| `celery_app.py` | `grade_quiz_task` için explicit `default` queue routing eklendi |
| `services/ai_service.py` | `grade_open_ended_answer` Gemini-öncelikli yapıya geçirildi |
| `examai-frontend/src/pages/Quiz.jsx` | Stale closure hatası `gradingIdRef` ile düzeltildi |

---

## Yapılması Gerekenler (Adım Adım)

### Adım 1 – Tüm Değişiklikleri GitHub'a Gönder

```powershell
cd C:\Users\ozgur\Desktop\EXAM_AI

git add backendWindsurf2/services/celery_tasks.py
git add backendWindsurf2/services/ai_service.py
git add backendWindsurf2/celery_app.py
git add examai-frontend/src/pages/Quiz.jsx
git add Docs/

git commit -m "Fix: grade_quiz_task top-level async refactor, stale closure, Gemini-first grading"
git push
```

### Adım 2 – Backend'i Fly.io'ya Deploy Et (KRİTİK)

```powershell
cd C:\Users\ozgur\Desktop\EXAM_AI\backendWindsurf2
fly deploy
```

> ⚠️ Bu adım en önemlisi. Celery worker'ı yeniden başlatır ve asıl düzeltmeyi aktif hale getirir.

### Adım 3 – Test Et

1. Uygulamaya giriş yap.
2. Klasik (açık uçlu) bir sınava gir.
3. Soruları cevapla ve "Sınavı Tamamla" butonuna bas.
4. "Cevaplarınız Değerlendiriliyor..." ekranı görünmeli.
5. **30–90 saniye** içinde sonuç ekranı gelmeli.

### Adım 4 – Hata Kontrolü (Sonuç Gelmezse)

```powershell
cd C:\Users\ozgur\Desktop\EXAM_AI\backendWindsurf2
fly logs
```

Loglarda `Grading completed | grading_id=...` satırını araştır. Bu satır yoksa backend tarafında hala bir sorun var demektir.
