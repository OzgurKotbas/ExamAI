# Canli Sinav Baslatma Celery Fallback Duzeltmesi

Tarih: 2026-05-01

## Belirti

Dashboard uzerinden kaynak secilip `Sinav Olustur` tiklandiginda arayuz su hatayi gosteriyordu:

```text
Failed to start quiz generation. Please try again.
```

Bu hata quiz henuz AI uretimine gecmeden, backend'in generation task'ini baslatma asamasinda donuyordu.

## Dosya Yapisi Analizi

- `examai-frontend/src/pages/Dashboard.jsx`
  - Modal ayarlarini topluyor ve `quizzesApi.create(...)` ile `POST /api/v1/quizzes` istegi atiyor.
- `examai-frontend/src/api/index.js`
  - Quiz olusturma istegini `/api/v1/quizzes` endpoint'ine yonlendiriyor.
- `backendWindsurf2/routers/quiz.py`
  - Not sahipligini ve icerigini kontrol ediyor, quiz kaydini olusturuyor, sonra Celery task'ini kuyrua atiyor.
- `backendWindsurf2/services/celery_tasks.py`
  - `generate_quiz_task` ile not metninden sorulari uretip DB'ye yaziyor.
- `backendWindsurf2/services/ai_service.py`
  - Gemini ve Hugging Face fallback ile soru JSON'u uretiyor.
- `backendWindsurf2/fly.toml`
  - Canli ortamda web ve worker process komutlarini tanimliyor.

## Kok Neden

`backendWindsurf2/routers/quiz.py` icinde quiz kaydi DB'ye commit edildikten sonra:

```python
generate_quiz_task.delay(str(quiz.id), cleaned_text)
```

cagrisi yapiliyordu. Redis/Celery broker baglantisi canlida hataliysa, `REDIS_URL` eksikse, Redis kapaliysa veya worker/kuyruk ayari uyumsuzsa bu satir exception uretiyor ve backend 500 olarak `Failed to start quiz generation` donuyordu.

Ek risk olarak Fly worker komutu `quiz_generation` kuyruunu acikca dinlemiyordu. Generate task'i `quiz_generation` kuyruuna route edildigi icin worker bu kuyruu dinlemezse task kuyrukta kalsa bile islenmeyebilir.

## Yapilan Degisiklikler

- `backendWindsurf2/services/celery_tasks.py`
  - Quiz uretim mantigi yeniden kullanilabilir `run_quiz_generation(quiz_id, note_text)` async fonksiyonuna cikarildi.
  - Celery task'i artik ayni fonksiyonu cagiriyor.
  - Bu fonksiyon soru uretimi basarisiz olursa quiz status'unu `failed` yapip `parameters.generation_error` alanina kisa hata kaydediyor.

- `backendWindsurf2/routers/quiz.py`
  - Celery `.delay(...)` basarisiz olursa kullaniciya hemen 500 dondurmek yerine web process icinde async fallback baslatiliyor.
  - Fallback baslatilabilirse endpoint yine `202 pending` donuyor; dashboard polling ile `generating/ready/failed` durumunu izlemeye devam ediyor.
  - Fallback task hata verirse loglaniyor ve quiz kaydi `failed` durumuna geciyor.

- `backendWindsurf2/fly.toml`
  - Worker komutu `default` ve `quiz_generation` kuyruklarini dinleyecek sekilde netlestirildi:

```toml
worker = "celery -A celery_app worker -Q default,quiz_generation --loglevel=info --pool=solo"
```

## Dogrulama

Basarili:

```powershell
C:\Users\ozgur\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m py_compile routers\quiz.py services\celery_tasks.py
```

Kosulamadi:

```powershell
python -m pytest tests\test_quiz.py -q
```

Neden: sistemde `python` ve `py` komutlari PATH'te yok. `backendWindsurf2/.venv/Scripts/python.exe` ise mevcut olmayan `C:\Users\ozgur\AppData\Local\Programs\Python\Python312\python.exe` yoluna bagli. Paketli Codex Python'unda da `pytest` kurulu degil.

## Canliya Alma Notlari

Bu kod duzeltmesi kullaniciya anlik 500 donduren kirilmayi engeller, fakat kalici saglik icin canlida Redis/Celery yine duzgun calismalidir.

Kontrol edilmesi gerekenler:

1. Fly secrets icinde `REDIS_URL` dogru tanimli olmali.
2. Fly worker process aktif olmali.
3. Deploy sonrasi worker loglarinda `quiz_generation` kuyruunun dinlendigi gorulmeli.
4. AI uretimi icin `GEMINI_API_KEY` ve/veya `HUGGINGFACE_API_TOKENS` tanimli olmali.

