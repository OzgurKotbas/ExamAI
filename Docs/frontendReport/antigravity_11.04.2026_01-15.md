# Frontend Değişiklik Raporu - ExamAI

**Tarih:** 11.04.2026  
**Saat:** 01:15  
**Hazırlayan:** Antigravity AI Assistant

## Özet
Sınav oluşturma sürecine "Sınav Dili" (Exam Language) seçimi entegre edildi. Bu sayede kullanıcılar, yükledikleri kaynağın dilinden bağımsız olarak sınavın hangi dilde (Türkçe veya İngilizce) üretileceğine karar verebilmektedir.

## Yapılan Değişiklikler

### 1. FileUpload.jsx (QuizCreationModal)
- **Dil Seçici UI:** "Zorluk Seviyesi" (Difficulty) bölümünün altına modern bir dil seçim paneli eklendi.
- **Dinamik State Yönetimi:** `quizLanguage` state'i eklendi. Default değer olarak uygulamanın o anki dili (`currentLanguage`) atanarak akıllı bir kullanıcı deneyimi sağlandı.
- **İkon Entegrasyonu:** `lucide-react`'ten `Globe` ikonu eklendi.
- **API Paylaşımı:** `quizzesApi.create` çağrısı güncellenerek seçilen dil backend'e gönderilmeye başlandı.

### 2. UI/UX İyileştirmeleri
- Dil butonları için hover ve active durumları özel renklerle (Indigo) belirginleştirildi.
- Türkçe için 🇹🇷 ve İngilizce için 🇬🇧 bayrak ikonları kullanılarak görsel netlik artırıldı.

## Teknik Detaylar
- Değişiklik yapılan dosya: `src/components/FileUpload.jsx`
- Kullanılan Context: `LanguageContext` (t ve currentLanguage için)
- Backend Parametresi: `language: "tr" | "en"`

---
*Bu rapor, yapılan frontend güncellemelerini belgelemek amacıyla otomatik olarak oluşturulmuştur.*
