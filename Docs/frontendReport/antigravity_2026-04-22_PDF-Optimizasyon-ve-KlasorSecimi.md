# ExamAI – PDF Boyut Optimizasyonu ve Klasör Seçimi
**Tarih:** 22 Nisan 2026, 21:59 (TSİ)  
**Hazırlayan:** Antigravity AI Assistant  
**Kapsam:** Frontend – Quiz.jsx `handleDownloadPDF` refactor

---

## Yapılan Değişiklikler

### 1. Seçenek C Uygulandı: Scale 1.5 + JPEG %85

**Sorun:** Önceki implementasyon `scale: 2` + `image/png` kullanıyordu → ~33 MB PDF.

```diff
// ÖNCESİ
const canvas = await html2canvas(element, {
-  scale: 2,
   ...
});
- const sliceData = sliceCanvas.toDataURL('image/png');
- pdf.addImage(sliceData, 'PNG', ...);

// SONRASI
const canvas = await html2canvas(element, {
+  scale: 1.5,   // piksel sayısı %44 azaldı
   ...
});
+ const sliceData = sliceCanvas.toDataURL('image/jpeg', 0.85);  // kayıplı, %60 daha küçük
+ pdf.addImage(sliceData, 'JPEG', ...);
```

**Tahmini sonuç:** 33 MB → **3–4 MB** (yaklaşık %90 küçülme)

| Parametre | Eski değer | Yeni değer | Etki |
|-----------|-----------|------------|------|
| `scale` | 2 | 1.5 | Piksel sayısı %44 azaldı |
| Format | `image/png` | `image/jpeg` | Kayıplı sıkıştırma |
| JPEG kalite | — | 0.85 (%85) | Görsel kalite korundu |
| `pdf.addImage` formatı | `'PNG'` | `'JPEG'` | jsPDF'e doğru format bilgisi |

---

### 2. Küçük Düzeltme: `Math.round` ile Tam Sayı Yükseklik

Canvas boyutlarının kesirli sayı olması bazen 1px boşluklara neden oluyordu:

```diff
- sliceCanvas.height = (sliceHeight * canvas.width) / imgWidth;
+ sliceCanvas.height = Math.round((sliceHeight * canvas.width) / imgWidth);
```

---

### 3. Klasör Seçimi – File System Access API

**Hedef:** Kullanıcıya PDF'i nereye kaydedeceğini soran yerel OS diyaloğu açmak.

#### Uygulama Mantığı

```js
const fileName = `ExamAI_Sonuc_${tarih}.pdf`;
const pdfBlob  = pdf.output('blob');   // ← Önce blob'a çevir

// Chrome/Edge: showSaveFilePicker mevcut mu?
if (typeof window.showSaveFilePicker === 'function') {
  try {
    const fileHandle = await window.showSaveFilePicker({
      suggestedName: fileName,
      types: [{ description: 'PDF Dosyası', accept: { 'application/pdf': ['.pdf'] } }],
    });
    const writable = await fileHandle.createWritable();
    await writable.write(pdfBlob);
    await writable.close();
    toast.success('PDF seçilen konuma kaydedildi!');

  } catch (pickerErr) {
    if (pickerErr.name === 'AbortError') {
      // Kullanıcı "İptal" tıkladı → sessizce kapat
      toast.dismiss('pdf-export');
    } else {
      // Picker açıldı ama write başarısız → fallback
      pdf.save(fileName);
    }
  }
} else {
  // Firefox / Safari → tarayıcının kendi indirme davranışı
  pdf.save(fileName);
}
```

#### Tarayıcı Destek Matrisi

| Tarayıcı | showSaveFilePicker | Davranış |
|----------|-------------------|----------|
| Chrome ≥ 86 | ✅ Destekleniyor | "Farklı Kaydet" OS diyaloğu açılır |
| Edge ≥ 86 | ✅ Destekleniyor | "Farklı Kaydet" OS diyaloğu açılır |
| Firefox | ❌ Desteklenmiyor | Otomatik olarak varsayılan klasöre indirir |
| Safari | ❌ Desteklenmiyor | Otomatik olarak varsayılan klasöre indirir |

#### Kullanıcı Deneyimi Akışı

```
PDF İndir butonuna tıkla
        ↓
"PDF hazırlanıyor..." toast
        ↓
html2canvas (scale:1.5) → JPEG %85 → jsPDF
        ↓
    Chrome/Edge?
   ↙          ↘
 Evet          Hayır
  ↓              ↓
OS "Farklı     pdf.save()
Kaydet"        (otomatik
diyaloğu       indirme)
  ↓
Kullanıcı konum seçer
  ↓
"PDF seçilen konuma kaydedildi!"
```

---

## Özet: Tüm PDF Değişiklikleri (Kronolojik)

### 22 Nisan 2026 – 21:47 (İlk Uygulama)
- `jsPDF` + `html2canvas` entegrasyonu
- `scale: 2`, `image/png`
- Tek tıkla indirme butonu header'a eklendi
- Çok sayfalı PDF desteği
- **Sonuç:** Çalışıyor ama ~33 MB

### 22 Nisan 2026 – 21:59 (Bu Güncelleme)
- `scale: 2 → 1.5` (piksel %44 azaldı)
- `image/png → image/jpeg, 0.85` (%60 boyut küçülmesi)
- `Math.round()` ile canvas yüksekliği tam sayıya yuvarlandı
- File System Access API (showSaveFilePicker) eklendi
- Chrome/Edge: OS "Farklı Kaydet" diyaloğu
- Firefox/Safari: `pdf.save()` fallback
- İptal durumu (AbortError) sessizce işleniyor
- **Tahmini Sonuç:** ~33 MB → **3–4 MB**

---

## Değişen Dosyalar

| Dosya | Satırlar | Değişiklik |
|-------|---------|-----------|
| `examai-frontend/src/pages/Quiz.jsx` | 140–231 | `handleDownloadPDF` fonksiyonu tamamen yenilendi |

---

*Rapor Antigravity AI tarafından otomatik oluşturulmuştur.*
