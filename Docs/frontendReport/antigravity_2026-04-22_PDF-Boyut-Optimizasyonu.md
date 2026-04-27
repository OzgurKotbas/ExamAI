# ExamAI – PDF İndirme: Boyut Optimizasyonu Analizi
**Tarih:** 22 Nisan 2026, 21:56 (TSİ)  
**Hazırlayan:** Antigravity AI Assistant  
**Kapsam:** Frontend – Quiz.jsx PDF Export Boyut Sorunu

---

## Mevcut Durum

### Uygulanan PDF Oluşturma Yöntemi (22 Nisan 2026 – 21:47)

`html2canvas` + `jsPDF` kombinasyonu kullanılarak sınav sonuç sayfası görsel olarak PDF'e aktarılmaktadır.

```js
// Mevcut kod – yüksek bellek kullanımı
const canvas = await html2canvas(element, {
  scale: 2,                    // ← 2x çözünürlük → piksel sayısı 4 kat artar
  useCORS: true,
  backgroundColor: '#f9fafb',
  logging: false,
});
const imgData = canvas.toDataURL('image/png');  // ← kayıpsız PNG → büyük boyut
```

### Sorun: 33MB PDF

**Neden bu kadar büyük?**

| Faktör | Açıklama | Katkısı |
|--------|----------|---------|
| `scale: 2` | 2x çözünürlük → orijinal canvas'ın 4 katı piksel | ~%75 boyut artışı |
| `image/png` | Kayıpsız (lossless) format — her piksel tam olarak saklanır | ~%60-80 fazladan boyut |
| Uzun içerik | Çok soru = çok uzun canvas = çok büyük PNG | Doğrudan orantılı |

**Özet:** 33MB PDF → `scale:2 × PNG lossless` kombinasyonunun sonucu.

---

## Boyut Küçültme Seçenekleri

### Seçenek A – Scale 2 → 1 (Yarı Çözünürlük)

```diff
- scale: 2,
+ scale: 1,
```

- **Tahmini boyut:** ~8 MB  
- **Görsel kalite:** Normal ekran çözünürlüğünde yeterli  
- **Zorluk:** Çok kolay (1 satır)  
- **Not:** Küçük metinlerde hafif bulanıklık olabilir

---

### Seçenek B – PNG → JPEG %80 Kalite

```diff
- const imgData = canvas.toDataURL('image/png');
+ const imgData = canvas.toDataURL('image/jpeg', 0.80);
```

- **Tahmini boyut:** ~5–6 MB  
- **Görsel kalite:** İyi (beyaz arka plan için JPEG uygundur)  
- **Zorluk:** Çok kolay (1 satır)  
- **Not:** Şeffaf arka plan varsa JPEG kullanılamaz; bu projede arka plan düz renk olduğundan sorun yok

---

### Seçenek C – Scale 1.5 + JPEG %85 (Dengeli)

```diff
- scale: 2,
+ scale: 1.5,

- const imgData = canvas.toDataURL('image/png');
+ const imgData = canvas.toDataURL('image/jpeg', 0.85);
```

- **Tahmini boyut:** ~3–4 MB  
- **Görsel kalite:** İyi — metin okunabilir, renkler doğal  
- **Zorluk:** Çok kolay (2 satır)  
- **Öneri:** Kalite/boyut dengesi için önerilen seçenek

---

### Seçenek D – Scale 1 + JPEG %75 (Agresif Sıkıştırma)

```diff
- scale: 2,
+ scale: 1,

- const imgData = canvas.toDataURL('image/jpeg', 0.80);
+ const imgData = canvas.toDataURL('image/jpeg', 0.75);
```

- **Tahmini boyut:** ~1.5–2 MB  
- **Görsel kalite:** Orta-İyi (ince çizgilerde hafif bozulma)  
- **Zorluk:** Çok kolay (2 satır)

---

### Seçenek E – Metin Tabanlı PDF (`jsPDF.html()`)

Görüntü yerine DOM elementini doğrudan metin/vektör olarak PDF'e aktarır.

```js
// Resim tabanlı yerine metin tabanlı
const pdf = new jsPDF({ ... });
pdf.html(resultsRef.current, {
  callback: (doc) => doc.save(fileName),
  x: 10, y: 10, width: 190,
  windowWidth: element.scrollWidth,
});
```

- **Tahmini boyut:** ~0.3–0.8 MB  
- **Görsel kalite:** Metin mükemmel keskin; ancak Tailwind CSS class'ları tam yorumlanamayabilir  
- **Zorluk:** Orta (layout, renk ve font sorunları çıkabilir)  
- **Risk:** Soru kartı arka planları, rozet renkleri bozulabilir

---

## Özet Karşılaştırma Tablosu

| Seçenek | Yöntem | Tahmini Boyut | Kalite | Zorluk |
|---------|--------|---------------|--------|--------|
| Mevcut | scale:2 + PNG | ~33 MB | Mükemmel | — |
| **A** | scale:1 | ~8 MB | İyi | ⭐ |
| **B** | JPEG %80 | ~5–6 MB | İyi | ⭐ |
| **C** | scale:1.5 + JPEG %85 | ~3–4 MB | İyi | ⭐ |
| **D** | scale:1 + JPEG %75 | ~1.5–2 MB | Orta-İyi | ⭐ |
| **E** | Metin tabanlı | ~0.3–0.8 MB | Değişken | ⭐⭐⭐ |

---

## Klasör Seçimi (Save As Diyaloğu)

### Teknik Durum

Tarayıcı güvenlik politikaları standart `a.download` ile dosya konumu seçimine izin vermez. Ancak **File System Access API** ile çözülebilir:

```js
// Chrome/Edge destekler; Firefox/Safari → fallback
const fileHandle = await window.showSaveFilePicker({
  suggestedName: 'ExamAI_Sonuc.pdf',
  types: [{ description: 'PDF Dosyası', accept: { 'application/pdf': ['.pdf'] } }],
});
const writable = await fileHandle.createWritable();
await writable.write(pdf.output('blob'));
await writable.close();
```

| Tarayıcı | Destek |
|----------|--------|
| Chrome ≥ 86 | ✅ |
| Edge ≥ 86 | ✅ |
| Firefox | ❌ (fallback: normal indirme) |
| Safari | ❌ (fallback: normal indirme) |

**Uygulama stratejisi:** `showSaveFilePicker` destekleniyorsa diyalog aç, desteklenmiyorsa `pdf.save()` ile normale dön.

---

## Bekleyen Karar

Kullanıcı aşağıdaki seçeneklerden birini onayladıktan sonra kod güncellenecektir:

- [ ] **A** – Sadece scale küçült (~8 MB)
- [ ] **B** – Sadece JPEG formatına geç (~5–6 MB)
- [ ] **C** – Scale + JPEG dengeli (~3–4 MB) ← Önerilen
- [ ] **D** – Agresif sıkıştırma (~1.5–2 MB)
- [ ] **E** – Metin tabanlı PDF (~0.3–0.8 MB, risk var)
- [ ] **Klasör seçimi** (File System Access API) eklensin mi?

---

*Rapor Antigravity AI tarafından otomatik oluşturulmuştur.*
