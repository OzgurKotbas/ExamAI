# Gemini Model Normalize Hatası & Otomasyon Stratejisi
**Tarih:** 21 Mayıs 2026  
**Konu:** "Seçilen model bu API anahtarı için erişilebilir değil" hatasının kök nedeni ve çözümü + model listesi otomasyonu

---

## 🐛 Sorun 1: "Model İsmi ve API Key Uyuşmadı" Hatası

### Kök Neden

Kullanıcının veritabanında kayıtlı model ismi `models/gemini-2.5-flash` formatındaydı
(başında `models/` prefix'i var).

**Hata zinciri:**

```
DB: user.gemini_model = "models/gemini-2.5-flash"
          ↓
ProfileMenu.jsx useState başlangıcı:
  editGeminiModel = user?.gemini_model || 'gemini-1.5-flash'
  → Değer: "models/gemini-2.5-flash"
          ↓
<select> dropdown hiçbir <option> ile eşleşmiyor
(dropdown'da "models/gemini-2.5-flash" yok, "gemini-2.5-flash" var)
          ↓
React select kontrolsüz davranır → görsel olarak ilk seçenek gösterilir:
"gemini-2.5-flash-preview-05-20"
          ↓
Doğrula butonuna basılır → preview modeli test edilir
          ↓
Preview modeller bazı ücretsiz API anahtarlarında 404 döner
          ↓
"Seçilen model bu API anahtarı için erişilebilir değil" mesajı
```

Ayrıca `gemini-2.5-flash` (**GA/stabil** sürüm) dropdown listesinde **hiç yoktu**.
Sadece `gemini-2.5-flash-preview-05-20` vardı. Preview sürümler her API anahtarıyla erişilemez.

---

## ✅ Uygulanan Çözümler

### Değişiklik 1: `examai-frontend/src/components/ProfileMenu.jsx`

**Ne değişti?**

1. `GEMINI_MODELS` dizisi ve `normalizeModel()` fonksiyonu **bileşen dışına** (module-level) taşındı.
   - Nedeni: `useState(() => normalizeModel(...))` callback'i bileşen kurulurken çağrılır.
     Fonksiyon bileşen içinde tanımlıysa bu noktada henüz erişilemez → hata.

2. `normalizeModel(raw)` fonksiyonu eklendi:
   ```js
   function normalizeModel(raw) {
     if (!raw) return 'gemini-2.5-flash';
     const cleaned = raw.replace(/^models\//, '');   // "models/" prefix temizle
     const exact = GEMINI_MODELS.find(m => m.value === cleaned);
     if (exact) return exact.value;
     const partial = GEMINI_MODELS.find(m =>
       cleaned.startsWith(m.value) || m.value.startsWith(cleaned)
     );
     if (partial) return partial.value;
     return 'gemini-2.5-flash';
   }
   ```

3. `useState` başlangıç değeri güncellendi:
   ```js
   // ÖNCE:
   const [editGeminiModel, setEditGeminiModel] = useState(user?.gemini_model || 'gemini-1.5-flash');

   // SONRA:
   const [editGeminiModel, setEditGeminiModel] = useState(() => normalizeModel(user?.gemini_model));
   ```

4. `handleCancel` içindeki reset de `normalizeModel` kullanmaya güncellendi.

5. Dropdown listesine **`gemini-2.5-flash` (GA stabil sürüm)** eklendi:
   ```js
   { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash 🚀 (Stabil - Önerilen)' },
   ```

---

### Değişiklik 2: `backendWindsurf2/services/ai_service.py`

**Ne değişti?**

`SUPPORTED_GEMINI_MODELS` listesine `"gemini-2.5-flash"` (GA sürüm) eklendi:

```python
# ÖNCE:
SUPPORTED_GEMINI_MODELS = [
    "gemini-2.5-flash-preview-05-20",
    ...
]

# SONRA:
SUPPORTED_GEMINI_MODELS = [
    "gemini-2.5-flash",                  # GA stabil sürüm – en geniş erişim
    "gemini-2.5-flash-preview-05-20",
    ...
]
```

**Neden?**  
`gemini-2.5-flash` (ön ek olmadan), GA (Generally Available / Stabil) sürümdür.
Preview sürümler yalnızca belirli API planlarında çalışır. GA sürüm tüm aktif API
anahtarlarında çalışması garantidir.

---

## 🤖 Soru 2: Model Listesini Otomatik Güncelleyebilir miyim?

**Evet, mümkün — ama dikkatli yapılması gerekiyor.** İki yol var:

---

### Yol A: Celery Beat ile Günlük Otomatik Kontrol (Önerilen)

Projenizde zaten **Celery** ve **Celery Beat** kurulu. Bunu kullanabilirsiniz.

#### 1. Yeni bir Celery görevi yaz

`backendWindsurf2/tasks/` altına `model_refresh.py` dosyası oluştur:

```python
# tasks/model_refresh.py
import logging
import google.generativeai as genai
from config import settings
from services.ai_service import SUPPORTED_GEMINI_MODELS

logger = logging.getLogger(__name__)

QUIZ_COMPATIBLE_METHODS = {"generateContent"}

def refresh_gemini_models():
    """
    Google API'den model listesini çeker, generateContent destekleyenleri filtreler,
    SUPPORTED_GEMINI_MODELS ile karşılaştırır ve farkı loglar/kaydeder.
    """
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        available = genai.list_models()

        fresh_models = []
        for m in available:
            supported = set(m.supported_generation_methods)
            if QUIZ_COMPATIBLE_METHODS.issubset(supported):
                # "models/" prefix'ini temizle
                name = m.name.replace("models/", "")
                fresh_models.append(name)

        new_models = [m for m in fresh_models if m not in SUPPORTED_GEMINI_MODELS]
        if new_models:
            logger.warning(f"Yeni Gemini modelleri tespit edildi: {new_models}")
            # Buraya: DB'ye kaydet veya bir notification gönder

        logger.info(f"Model refresh tamamlandı. Mevcut: {len(SUPPORTED_GEMINI_MODELS)}, API: {len(fresh_models)}")
        return {"existing": SUPPORTED_GEMINI_MODELS, "api": fresh_models, "new": new_models}

    except Exception as e:
        logger.error(f"Model refresh başarısız: {e}")
        raise
```

#### 2. Celery Beat schedule'a ekle (`celery_app.py` veya `config.py`):

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    # ... mevcut görevler ...
    'refresh-gemini-models-daily': {
        'task': 'tasks.model_refresh.refresh_gemini_models',
        'schedule': crontab(hour=3, minute=0),  # Her gece saat 03:00
    },
}
```

> **⚠️ Önemli:** `SUPPORTED_GEMINI_MODELS` Python listesi; runtime'da değiştirilse bile
> sunucu yeniden başlatılmadan frontend'e yansımaz. Bu nedenle yeni modelleri
> **veritabanında ayrı bir tablo/sütunda** saklamak ve `/gemini-models` endpoint'ini
> buradan okutmak daha sağlıklıdır.

---

### Yol B: DB Tabanlı Dinamik Model Listesi (Uzun Vadeli Çözüm)

| Adım | Açıklama |
|------|----------|
| 1 | `GeminiModel` adında DB tablosu oluştur (`id`, `name`, `label`, `is_active`, `added_at`) |
| 2 | Celery görevi her gece API'yi sorgular, yeni modelleri tabloya ekler |
| 3 | `/api/v1/auth/gemini-models` endpoint'i artık `SUPPORTED_GEMINI_MODELS` listesi yerine DB'den okur |
| 4 | Frontend her seferinde güncel listeyi alır |

Bu yaklaşım sayesinde:
- ✅ Kod değişikliği gerekmez
- ✅ Yeni modeller otomatik görünür
- ✅ Admin panelinden `is_active` ile model açıp kapatılabilir

---

### Neden Tam Otomasyonda Dikkatli Olmak Gerekiyor?

| Risk | Açıklama |
|------|----------|
| Experimental modeller | `gemini-2.5-thinking-exp` gibi modeller API'de görünür ama kararsız olabilir |
| Preview erişim kısıtları | Preview modeller tüm API anahtarlarında çalışmaz |
| Model formatı | Bazı modeller `generateContent` dışında (embed, classify) olabilir |
| Kullanıcı konfüzyonu | Çok fazla model seçeneği kullanıcıyı zorlar |

**Öneri:** Otomasyonu sadece **loglama + bildirim** için kullan. Yeni modeli listeye
eklemek için bir admin onayı iste. Tam otomasyonu yalnızca test edilmiş GA modeller için uygula.

---

## Özet

| Değişen Dosya | Neden |
|---|---|
| `examai-frontend/src/components/ProfileMenu.jsx` | DB'deki `models/` prefix'li değer dropdown ile eşleşmiyordu → `normalizeModel()` eklendi, `gemini-2.5-flash` (GA) listeye eklendi |
| `backendWindsurf2/services/ai_service.py` | Backend model listesine GA sürüm eklendi |
