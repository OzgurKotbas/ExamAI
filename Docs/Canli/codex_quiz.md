# Canli Sinav Olusturma AI Fallback Duzeltmesi

Tarih: 2026-04-30

## Belirti

Not yukleme artik basarili. Dashboard notu goruyor, fakat olusturulan sinav `Basarisiz` durumuna dusuyor.

## Inceleme

Sistem mimarisi:

- `POST /api/v1/quizzes` quiz kaydi olusturuyor.
- Celery `generate_quiz_task` arka planda not metninden sorular uretiyor.
- AI uretimi `services/ai_service.py` icinden Gemini ve Hugging Face servislerini kullaniyor.

Mevcut kodda iki risk bulundu:

1. Redis cache quiz basariyla uretilmeden once yaziliyordu. Bu, pending/failed bir quiz'in sonraki denemelerde cache gibi donmesine neden olabilir.
2. AI fallback sirasi ve hata raporlama net degildi. Gemini basarisiz olursa Hugging Face modellerine gecis daha acik hale getirildi.

## Yapilan Degisiklikler

- `backendWindsurf2/services/ai_service.py`
  - Uretim sirasi `Gemini -> Hugging Face fallback` olarak duzenlendi.
  - Gemini bos cevap veya hata verirse HF modelleri denenir.
  - `HUGGINGFACE_API_TOKENS`, `HUGGINGFACE_API_KEY`, `HF_TOKEN` isimleri desteklenir.
  - AI cevaplari markdown code fence ile gelirse JSON parse oncesi temizlenir.
  - Tum provider'lar basarisiz olursa son hatalar tek mesajda loglanir.

- `backendWindsurf2/routers/quiz.py`
  - Redis cache artik sadece DB'de `ready` ve soru kaydi olan quiz icin kullanilir.
  - Stale/pending/failed cache kayitlari yok sayilir.
  - Quiz basariyla uretilmeden once cache yazma kaldirildi.

- `backendWindsurf2/services/celery_tasks.py`
  - Cache yazma islemi sadece sorular basariyla kaydedildikten sonra yapilir.
  - Generation hatasi quiz `parameters.generation_error` alanina kisaltilmis sekilde yazilir.

- `backendWindsurf2/main.py`
  - `/health` cevabina `huggingface_tokens` ve `huggingface_models` sayilari eklendi.

- `backendWindsurf2/config.py`
  - HF token icin ek secret adlari desteklendi:
    - `HUGGINGFACE_API_TOKENS`
    - `HUGGINGFACE_API_KEY`
    - `HF_TOKEN`

## Onemli Canli Ayar

Yerel `.env` dosyasinda model isimleri gorunuyor fakat HF token degiskeni gorunmuyor. Canli fallback'in calismasi icin Fly secrets icinde en az bir HF token tanimli olmali.

Onerilen:

```powershell
fly secrets set HUGGINGFACE_API_TOKENS=hf_xxxxxxxxxxxxxxxxx
```

Opsiyonel olarak model listesini de canlida netlestir:

```powershell
fly secrets set HUGGINGFACE_MODELS="Qwen/Qwen2.5-72B-Instruct,Qwen/Qwen2.5-7B-Instruct,mistralai/Mistral-Nemo-Instruct-2407,microsoft/Phi-3.5-mini-instruct"
```

## Deploy Sonrasi Kontrol

`https://backendwindsurf2.fly.dev/health` icinde sunlar gorulmeli:

```json
"gemini_api_key": true,
"huggingface_tokens": 1,
"huggingface_models": 4
```

`huggingface_tokens` 0 ise Gemini basarisiz oldugunda HF fallback calisamaz.

## Eski Basarisiz Quizler

Bu duzeltme yeni olusturulacak quizler icindir. Dashboard'daki eski `Basarisiz` quiz silinip ayni nottan yeni quiz olusturulmalidir.

