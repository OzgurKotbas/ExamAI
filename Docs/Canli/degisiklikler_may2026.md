# ExamAI – Mayıs 2026 Değişiklik Raporu

**Tarih:** 03 Mayıs 2026  
**Versiyon:** v1.x güncellemesi  
**Kapsam:** 4 hata düzeltmesi ve iyileştirme

---

## 1. Analitik Doğruluk Hesabı Düzeltmesi

### Sorun
Analytics sayfasındaki "Konu Başarı Oranları" grafiği yanlış değerler gösteriyordu.  
Örnek: "İnternetin Tarihsel Gelişimi" konusundan 2 soru sorulmuş, kullanıcı 1 tanesini doğru yapmış. Görüntülenen değer `16.5` idi — bu, ham puan ortalamasının direkt olarak oran gibi kullanılmasından kaynaklanıyordu.

### Düzeltme

**Dosya:** `backendWindsurf2/routers/quiz.py` → `get_quiz_analytics()` fonksiyonu

**Eski mantık:**
```python
avg_score = data["total_score"] / data["total_count"]
accuracy_pct = min(round(avg_score, 1), 100.0)
# Bu yanlış: q_score (örn. 33.3) doğrudan yüzde gibi kullanılıyordu
```

**Yeni mantık:**
```python
# score > 0 ise cevap "doğru" sayılır
accuracy_pct = (correct_count / total_count) * 100
# Örnek: 2 sorudan 1 doğru → %50.0
```

SQL sorgusu da değiştirildi: artık `GROUP BY` yerine her satır ayrı ayrı okunuyor, `score > 0` kontrolüyle doğru sayısı hesaplanıyor.

---

## 2. Google ile Giriş – Yönlendirme Mantığı

### Sorun
"Google ile Giriş Yap" butonuna tıklandığında:
- Hesabı **olan** kullanıcı → dashboard yerine register sayfasına gitmeye çalışıyordu (hata)
- Hesabı **olmayan** kullanıcı → otomatik hesap oluşturulup dashboard'a yönlendiriliyordu

### Düzeltme

**Dosya:** `examai-frontend/src/pages/AuthCallback.jsx`

Backend zaten `is_new` parametresini döndürüyor. AuthCallback artık:

| Durum | Aksiyon |
|-------|---------|
| `is_new = false` | Token ile login yap → Dashboard'a yönlendir |
| `is_new = true` | Google bilgilerini query param olarak taşı → Register sayfasına yönlendir |

**Dosya:** `examai-frontend/src/pages/Register.jsx`

Google'dan yönlendirilen kullanıcılar için:
- `?from=google` query parametresi algılanır
- E-posta ve ad alanları Google'dan otomatik doldurulur (readonly)
- Şifre alanları gizlenir (Google OAuth kullanıcısının şifreye ihtiyacı yok)
- "Kayıt Ol" butonuna tıklandığında mevcut Google token ile oturum açılır
- Mavi bilgi banner'ı gösterilir: "Google hesabınızla kayıt oluyorsunuz"

---

## 3. Dil Çevirileri – Eksik İngilizce Metinler

### Sorun
Sayfa İngilizce'ye geçirildiğinde, "Kategoriler" bölümündeki bazı metinler hâlâ Türkçe kalıyordu.

### Düzeltilen Dosyalar

**`examai-frontend/src/context/LanguageContext.jsx`**

Eklenen çeviri anahtarları:

| Anahtar | Türkçe | İngilizce |
|---------|--------|-----------|
| `uncategorized` | Kategorisiz | Uncategorized |
| `quizzesCount` | sınav | quiz |
| `noQuizzesYet` | Henüz sınav yok | No quizzes yet |
| `noQuizzesInCategory` | Bu kategoride henüz sınav bulunmuyor. | No quizzes in this category yet. |
| `categoryNameLabel` | Kategori Adı | Category Name |
| `categoryNamePlaceholder` | Örn: Matematik, Fizik, Tarih... | E.g: Math, Physics, History... |
| `editCategory` | Kategori Düzenle | Edit Category |
| `save` | Kaydet | Save |
| `edit` | Düzenle | Edit |
| `delete` | Sil | Delete |
| `questionsLabel` | soru | questions |

**`examai-frontend/src/components/QuizCategories.jsx`**

Sabit Türkçe string'lerin tamamı `t()` fonksiyonu ile değiştirildi:
- Kategori menüsü (Düzenle/Sil butonları)
- Modal başlıkları ve form etiketleri
- Boş durum mesajları
- Sınav sayısı metni
- Toast bildirimleri

---

## 4. Sınav Oluşturma – Otomatik Yenileme İyileştirmesi

### Sorun
Sınav oluşturulduğunda sayfa yenilenmeden listede görünmüyordu. Mevcut 5 saniyelik polling mekanizması **stale closure** problemi nedeniyle çalışmıyordu: `setInterval` içindeki callback, `generatingQuizIds` state'inin ilk değerini (boş Set) okuyordu.

### Düzeltme

**Dosya:** `examai-frontend/src/pages/Dashboard.jsx`

- `useRef` ile `generatingQuizIdsRef` oluşturuldu
- `checkGeneratingQuizzes` fonksiyonu `useCallback` ile sarıldı
- `checkGeneratingQuizzesRef` ile interval her zaman güncel callback'i çağırıyor
- State değiştiğinde ref de güncelleniyor

**Sonuç:** Sınav oluşturulduğunda:
1. Anında "Oluşturuluyor..." göstergesi çıkıyor
2. Her 5 saniyede backend sorgulanıyor
3. Sınav hazır olunca toast bildirimi geliyor ve liste güncelleniyor
4. Sayfa yenilemeye gerek yok

```
Yeni Sınav Oluştur → ⏳ toast → 5sn poll → 🎉 "Sınav hazır!" → Liste güncellendi
```

Ek iyileştirme: Quiz hazır/başarısız bildirimleri artık seçili dile göre gösteriliyor.

---

## Değiştirilen Dosyalar Özeti

| Dosya | Değişiklik |
|-------|-----------|
| `backendWindsurf2/routers/quiz.py` | Analytics doğruluk formülü düzeltildi |
| `examai-frontend/src/pages/AuthCallback.jsx` | Google login yönlendirme mantığı |
| `examai-frontend/src/pages/Register.jsx` | Google OAuth kayıt akışı desteği |
| `examai-frontend/src/context/LanguageContext.jsx` | 11 yeni çeviri anahtarı eklendi |
| `examai-frontend/src/components/QuizCategories.jsx` | Tüm sabit Türkçe metinler çevrildi |
| `examai-frontend/src/pages/Dashboard.jsx` | useRef ile polling stale closure düzeltildi |

---

## Yapılması Gerekenler (Kullanıcı Adımları)

1. **Backend'i yeniden başlatın** (analytics düzeltmesi için):
   ```bash
   # backendWindsurf2 klasöründe
   uvicorn main:app --reload
   ```

2. **Frontend'i yeniden başlatın** (tüm frontend değişiklikler için):
   ```bash
   # examai-frontend klasöründe
   npm run dev
   ```

3. **Varsa üretim ortamında** (Fly.io / Render) deploy edin:
   ```bash
   # Backend için
   fly deploy
   # Frontend için Vercel'e push edin
   git add . && git commit -m "fix: analytics, google login redirect, i18n, polling" && git push
   ```

---

## Test Senaryoları

### 1. Analitik Doğruluk Testi
- 3 soruluk sınav çözün, 1 doğru yapın
- Analytics sayfasında ilgili konunun `33.3%` göstermesi bekleniyor

### 2. Google Login Testi
- Mevcut hesapla Google giriş → Dashboard'a yönlendirmeli
- Yeni Google hesabıyla giriş → Register sayfasına yönlendirmeli, bilgiler dolu gelecek

### 3. Dil Değiştirme Testi
- İngilizce seçin → Kategoriler bölümünde tüm metinlerin İngilizce olması bekleniyor

### 4. Otomatik Yenileme Testi
- Yeni sınav oluşturun → sayfa yenilemeden 5-30 saniye içinde listede görünmeli
