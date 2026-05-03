# Canli Deploy Context Duzeltmesi

Tarih: 2026-04-30

## Yeni Bulgu

Son `fly deploy` logunda build context su sekilde gorundu:

```text
transferring context: 2.32kB
CACHED [6/6] COPY . .
```

Bu deger backend projesi icin cok kucuk. `services/`, `routers/`, `utils/` gibi kaynak klasorleri dahil edilse context yaklasik yuzlerce KB olmaliydi. Bu nedenle onceki kod duzeltmeleri canli Docker imajina girmemis olabilir.

## Kok Neden

`backendWindsurf2/.dockerignore` dosyasi Windows ters slash kaliplari ve `flyctl launch` tarafindan eklenen satirlarla olusmustu. Fly/Depot build tarafinda bu ignore kurallari kaynak klasorlerinin beklenmeyen sekilde disarida kalmasina veya cache'in eski kaynakla devam etmesine neden olabiliyordu.

## Yapilan Degisiklikler

- `backendWindsurf2/.dockerignore`
  - Dosya bastan sade ve forward-slash uyumlu olacak sekilde yazildi.
  - `.venv`, cache, log, upload ve `.env` dosyalari dislandi.
  - `routers/`, `services/`, `utils/`, `models/`, `schemas/` gibi kaynak klasorleri artik image context'e dahil edilecek.

- `backendWindsurf2/Dockerfile`
  - Sadelestirildi.
  - `COPY . .` sonrasina kritik dosyalar icin `python -m py_compile` kontrolu eklendi.
  - Bu adim deploy logunda gorunurse yeni Dockerfile'in ve kaynak dosyalarin imaja girdigi anlasilir.

## Beklenen Yeni Deploy Logu

Bir sonraki deployda su farklar gorulmeli:

```text
transferring context: ...kB
RUN python -m py_compile main.py routers/notes.py services/extraction_service.py utils/security.py
```

Context yine `2.32kB` gibi cok kucuk gorunurse kaynak dosyalari hala Docker context'e girmiyor demektir.

## Onerilen Deploy Komutu

Cache etkisini tamamen kirmak icin:

```bash
cd backendWindsurf2
fly deploy --no-cache
```

## Deploy Sonrasi Kontrol

1. Fly deploy logunda context boyutu artik `2.32kB` olmamali.
2. Logda `RUN python -m py_compile ...` adimi gorulmeli.
3. Backend acildiktan sonra PDF tekrar yuklenmeli.
4. Taranmis PDF'lerde Gemini Vision devreye girecegi icin islem metin tabanli PDF'e gore daha uzun surebilir.

