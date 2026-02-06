# EnglishBus - Kullanım Kılavuzu

## Sistemi Başlatma

### 1. Backend API'yi Başlat

```bash
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

✅ Şunu göreceksin:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
📁 Static files mounted: /assets → /Users/.../kurslar
```

### 2. Frontend'e Eriş

**Bilgisayardan:**
- Tarayıcıda aç: `http://localhost:8000`
- veya: `http://192.168.1.5:8000`

**Mobil Cihazdan (aynı WiFi):**
- Tarayıcıda aç: `http://192.168.1.5:8000`

---

## Özellikler

### ✅ Çalışan Özellikler

1. **Fibonacci Spaced Repetition**
   - Kelimeler 1,1,2,3,5,8,13... step aralıklarla tekrar eder

2. **1-4-7-10 Yeni Kelime Kuralı**
   - Yeni kelime sadece 1, 4, 7, 10... adımlarında gelir

3. **Unit Lock Sistemi**
   - A1.1: Her zaman açık
   - A1.2: A1.1'in %50'si görülünce açılır
   - A1.3: A1.1 %100 VE A1.2 %50 olunca açılır

4. **Resim & Ses**
   - Her kelimede resim gösterilir
   - İngilizce ses otomatik çalar
   - Türkçe ses "ANLAMI GÖSTER" ile çalar

5. **İlerleme Sıfırlama**
   - Header'daki 🔄 butonu ile tüm ilerleme silinir

---

## Sorun Giderme

### "Sayfa Açılmıyor"

**Çözüm:**
```bash
# Backend çalışıyor mu?
ps aux | grep uvicorn

# Çalışmıyorsa başlat:
cd backend && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### "Resimler Görünmüyor"

**Kontrol:**
```bash
# Static files çalışıyor mu?
curl -I http://localhost:8000/assets/A1_English/images/001.jpg

# HTTP/1.1 200 OK görmeli
```

**Çözüm:** Backend'i restart et (yukarıdaki komut)

### "Sesler Çalmıyor"

**Kontrol:**
```bash
# Ses dosyaları var mı?
ls kurslar/A1_English/ing_audio/ | head -5
ls kurslar/A1_English/tr_audio/ | head -5
```

**Tarayıcı Console'u Kontrol Et:**
- F12 bas → Console tab
- Kırmızı hata varsa kopyala, bana gönder

---

## Endpoint Listesi

### GET /
Frontend (index.html) döner

### GET /health
Sistem durumu

### POST /session/start
```json
{
  "user_id": 1,
  "course_id": 1
}
```

### POST /session/complete
```json
{
  "user_id": 1,
  "course_id": 1,
  "completed_word_ids": [1, 2, 3]
}
```

### POST /reset
```json
{
  "user_id": 1,
  "course_id": 1
}
```

### GET /courses/{course_id}/units/status?user_id={user_id}
Ünite durumlarını gösterir

### GET /assets/{path}
Resim/ses dosyaları
- Örnek: `/assets/A1_English/images/001.jpg`
- Örnek: `/assets/A1_English/ing_audio/ing_001.mp3`

---

## Geliştirme Notları

### Database Sıfırlama
```bash
sqlite3 englishbus.db "DELETE FROM UserProgress; DELETE FROM UserCourseProgress;"
```

### Test Çalıştırma
```bash
python3 tests/test_unit_lock.py
```

### API Dokümantasyonu
`http://localhost:8000/docs`

---

## Özet Komutlar

```bash
# Hızlı başlat (tek komut)
cd /Users/emrah/Documents/Projeler/EnglishBus/backend && \
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Tarayıcıda aç
open http://localhost:8000

# Mobil için IP
ifconfig en0 | grep "inet " | awk '{print $2}'
```

**Hazır!** 🚀
