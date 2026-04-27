# ExamAI – Dashboard Siyah Ekran Hatası: Kök Neden Analizi ve Çözüm Raporu

**Tarih:** 10.04.2026 – 20:33
**Hazırlayan:** Antigravity
**Konu:** Dashboard ve Kategoriler sekmelerine geçişte oluşan siyah ekran (sayfa çökmesi)

---

## Sorun Tanımı

Kullanıcı "Oluşturulan Sınav" veya "Kategoriler" sekmelerinden birine tıkladığında ekran tamamen siyah kalıyordu. URL hep `localhost:5173/dashboard` olarak görünüyordu, dolayısıyla sayfa farklı bir URL'e yönlendirmiyordu. Sorun **React component crash (Hata sınırı)** değil, **backend'in 500 hata döndürmesi** ve bunun frontend'i boş bırakmasıydı.

---

## Kök Neden

### Birincil Neden: `list_quizzes` Backend 500 Hatası

`routers/quiz.py` içindeki `list_quizzes` endpoint'i, her sınav için en son puanlama oturumunu ve toplam skoru çekmek üzere değiştirilmişti. Ancak bu değişiklik kritik bir hata içeriyordu:

```python
# HATALI KOD (ESKİ)
quiz.latest_grading_id = latest_id  # ← Quiz ORM modelinde bu sütun YOK!
quiz.score = score_result.scalar()  # ← Bu da yok!
quiz.max_score = 100.0              # ← Bu da yok!
```

`Quiz` SQLAlchemy ORM modeli (`models/quiz.py`) bu alanları **tanımlamıyor**. SQLAlchemy'de var olmayan bir sütuna bu şekilde atama yapıldığında, ORM'nin `__setattr__` mekanizması beklenmedik davranışlar sergileyebilir. Pydantic response_model doğrulaması da ORM nesnesini serialize etmeye çalışırken hata fırlatıyordu.

**Sonuç:** Her `GET /api/v1/quizzes` isteğine karşılık backend **500 Internal Server Error** dönüyordu.

### İkincil Neden: Frontend'in 500 Hatasını Sessizce Yutması

`Dashboard.jsx` içindeki `fetchData()` fonksiyonu:

```js
const fetchData = async () => {
  try {
    const [notesRes, quizzesRes] = await Promise.all([...]);
    setQuizzes(quizzesRes.data);  // 500 gelince bu satır çalışmaz
  } catch (error) {
    toast.error(t('error'));  // Sadece toast gösteriyor
  }
};
```

Backend 500 döndürdüğünde `quizzesRes.data` boş kalıyor ve `quizzes` state'i başlangıç değeri olan boş array `[]` kalıyordu. Sekme içerikleri de boş görünüyordu. Üstelik API interceptor'daki `window.location.href = '/login'` yönlendirmesi (401 durumu için) de bazı durumlarda yanlış tetiklenebiliyordu.

---

## Uygulanan Çözüm

`list_quizzes` endpoint'i, SQLAlchemy ORM nesnelerini mutate etmek yerine **plain Python dict** listesi döndürecek şekilde yeniden yazıldı:

```python
# DOĞRU KOD (YENİ)
response_list = []
for quiz in quizzes:
    # ... grading session sorgula ...
    
    response_list.append({
        "id": quiz.id,
        "note_id": quiz.note_id,
        "total_questions": quiz.total_questions,
        "mc_ratio": float(quiz.mc_ratio),
        "difficulty": quiz.difficulty,
        "status": quiz.status,
        "created_at": quiz.created_at,
        "completed_at": quiz.completed_at,
        "latest_grading_id": latest_id,  # Güvenli: sadece dict key
        "score": score,                   # Güvenli: sadece dict key
        "max_score": max_score,           # Güvenli: sadece dict key
    })

return response_list  # Pydantic QuizRead schema bunu başarıyla serialize eder
```

Bu yaklaşımda:
- ORM nesnesi hiçbir zaman mutate edilmiyor
- SQLAlchemy `__setattr__` trap'i tetiklenmiyor
- Pydantic `QuizRead` schema'sı (zaten `score`/`max_score` alanlarını içeren) bu dict'i hatasız serialize ediyor

---

## Değişen Dosyalar

| Dosya | Değişiklik |
| :--- | :--- |
| `backendWindsurf2/routers/quiz.py` | `list_quizzes` endpoint'i dict-tabanlı response ile yeniden yazıldı |

---

## Test Kriterleri

- `GET /api/v1/quizzes` → **200 OK** dönmeli, `score`/`latest_grading_id` alanlarını içermeli
- Dashboard'da "Oluşturulan Sınav" sekmesi → Siyah ekran olmadan yüklenmelidir
- Dashboard'da "Kategoriler" sekmesi → Siyah ekran olmadan yüklenmelidir
- Çözülmüş sınavlara puan (örn. `85.0 / 100.0`) gösterilmelidir

---

*Bu dosya Antigravity tarafından 10.04.2026 20:33 tarihinde oluşturulmuştur.*
