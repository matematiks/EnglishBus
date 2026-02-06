# EnglishBus - Proje Tarihi ve Yeniden İnşa Kılavuzu

**Oluşturulma:** 2025-12-12 → 2025-12-15 (3 gün)  
**Amaç:** Eğer bu proje kaybolursa, bu belgeden yararlanarak sıfırdan inşa edilebilir

---

## 📖 Proje Hikayesi

### Başlangıç Noktası (12 Aralık)

**Problem:** 
- Klasik kelime uygulamaları stres yaratıyor (streak, test, zaman baskısı)
- Fibonacci tabanlı spaced repetition algoritması mevcut ama backend yok
- Sistem spec dosyası var (`uygulama.text`) ama implement edilmemiş

**Hedef:**
- Minimalist, stressiz kelime öğrenme uygulaması
- "Bitmeyen tekrar" felsefesi
- Step-based (time-based değil) spaced repetition

### Kritik Kararlar

#### 1. Zaman Değil, Adım Kullanımı
```python
# YANLIŞ (klasik SRS):
next_review_date = today + timedelta(days=fibonacci(level))

# DOĞRU (EnglishBus):
next_review_step = current_step + fibonacci(repetition_count)
```

**Neden?** 
- Kullanıcı baskı hissetmez
- "Bugün kaçıncı gün" stresi yok
- Oturum bitirmeden bırakabilir

#### 2. Doğru/Yanlış Test Yok
```javascript
// YANLIŞ:
if (userAnswer === correctAnswer) { /* correct */ }

// DOĞRU:
// Sadece "TAMAMLADIM" butonu → Otomatik doğru sayılır
```

**Neden?**
- "Yapabiliyorum" motivasyonu
- Test kaygısı yaratmaz
- Sürdürülebilir öğrenme

#### 3. Sonsuz Tekrar (Mastered Yok)
```python
# YANLIŞ:
if repetition_count > 10:
    word.status = "MASTERED"  # ❌

# DOĞRU:
# Kelime asla bitmez, sadece aralık uzar
next_review = current + fibonacci(count)  # ✅
```

**Neden?**
- Unutmayı engellemek
- Uzun vadeli hafıza
- Kelime bitme hissi yaratmaz

---

## 🏗️ İnşa Süreci (Kronolojik)

### Gün 1 (12 Aralık): Spec ve Fibonacci

**Yapılan:**
1. `uygulama.text` dosyası detaylı incelendi
2. Fibonacci dizisi formülü netleştirildi:
   ```
   Fib[1]=1, Fib[2]=1, Fib[3]=2, Fib[4]=3, Fib[5]=5...
   next_review_step = current_step + Fib[repetition_count]
   ```
3. 1-4-7-10 kuralı anlaşıldı:
   - Yeni kelime sadece (step-1) % 3 == 0 adımlarında
   - Steps: 1, 4, 7, 10, 13, 16...
   - Review words diğer adımlarda

**Çıktı:**
- `fibonacci_gaps_visual.md` (görsel açıklama)
- `fibonacci_update.md` (formül update)

### Gün 2 (13 Aralık): Database ve Backend

**Yapılan:**
1. SQLite schema tasarımı:
   ```sql
   UserProgress:
     - repetition_count (kaç kez görüldü)
     - next_review_step (Fibonacci ile hesaplanan)
   
   UserCourseProgress:
    - current_step (kullanıcı hangi adımda)
   ```

2. Backend API oluşturuldu:
   - FastAPI seçildi (modern, async, fast)
   - Pydantic models (tip güvenliği)
   - 3 endpoint: /health, /session/start, /session/complete

3. **Atomic Transaction** implement edildi:
   ```python
   BEGIN TRANSACTION
     UPDATE UserProgress...
     UPDATE UserCourseProgress SET current_step = step + 1
   COMMIT  # Ya hepsi başarılı, ya hiçbiri
   ```

**Çıktı:**
- `backend/session_manager.py` (core logic)
- `backend/api/endpoints.py` (REST API)
- `backend/API_CONTRACT.md` (spec)

### Gün 3 (14 Aralık): Frontend ve Test

**Yapılan:**
1. Single-file HTML frontend:
   ```html
   <button id="btn-reveal">ANLAMI GÖSTER</button>
   <button id="btn-complete">TAMAMLADIM</button>
   <!-- Static DOM, CSS toggle ile göster/gizle -->
   ```

2. **Kritik Bug Fix: Fibonacci Yanlış Yorumu**
   - İlk implemantasyon: 1-4-7-10 pattern'i review'lara uygulamaya çalıştı ❌
   - Düzeltme: 1-4-7-10 SADECE NEW word introduction için ✅
   - Review gaps: Saf Fibonacci ✅

3. Pattern doğrulaması:
   ```
   Expected: I, I, I, am, am, I, am, here, here, am, I, here...
   System:   I, I, I, am, am, I, am, here, here, am, I, here...
   ✅ 100% Match!
   ```

4. Ordering fix:
   - İlk: `ORDER BY repetition_count`
   - Son: `ORDER BY order_number DESC` (yeni kelimeler önce)

**Çıktı:**
- `index.html` (production-ready frontend)
- `walkthrough.md` (test sonuçları)

### Gün 4 (15 Aralık): Polish ve Audit

**Yapılan:**
1. UX improvements:
   - Türkçe ses eklendi (reveal'de çalıyor)
   - Session transition popup kaldırıldı
   - Reset butonu eklendi (header'da 🔄)

2. Mobile support:
   - Backend: `--host 0.0.0.0`
   - Frontend: `API_URL = "http://192.168.1.5:8000"`

3. **Full System Audit:**
   - Database schema ✅
   - Fibonacci function ✅
   - 10-step simulation ✅
   - Pattern verification ✅
   - API endpoints ✅
   
4. Documentation:
   - `SYSTEM_CAPABILITIES.md`
   - `PROJECT_HISTORY.md` (bu dosya)

---

## 🔧 Yeniden İnşa Kılavuzu

Eğer bu proje kaybolursa, şu adımları takip et:

### Adım 1: Temel Dosyalar

1. **Spec dosyalarını oku:**
   - `uygulama.text` - Algoritma detayları
   - `tanıtım.text` - Proje felsefesi
   - `CSV_DATA_CONTRACT.md` - Data format

2. **Kritik formüller:**
   ```python
   # Fibonacci (1-indexed)
   def fibonacci(n):
       if n <= 0: return 0
       if n == 1 or n == 2: return 1
       a, b = 1, 1
       for _ in range(2, n):
           a, b = b, a + b
       return b
   
   # New word rule
   if (current_step - 1) % 3 == 0:
       # Fetch next NEW word
   
   # Review calculation
   next_review_step = current_step + fibonacci(new_repetition_count)
   
   # First encounter
   next_review_step = current_step + 1  # Fib[1] = 1
   ```

### Adım 2: Database Schema

```sql
CREATE TABLE Words (
    id INTEGER PRIMARY KEY,
    course_id INTEGER,
    unit_id INTEGER,
    english TEXT,
    turkish TEXT,
    image_url TEXT,
    audio_en_url TEXT,
    audio_tr_url TEXT,
    order_number INTEGER  -- ÖNEMLI: Sıralama için
);

CREATE TABLE UserProgress (
    user_id INTEGER,
    word_id INTEGER,
    repetition_count INTEGER DEFAULT 0,
    next_review_step INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, word_id)
);

CREATE TABLE UserCourseProgress (
    user_id INTEGER,
    course_id INTEGER,
    current_step INTEGER DEFAULT 1,
    last_activity TIMESTAMP,
    PRIMARY KEY (user_id, course_id)
);
```

### Adım 3: Backend Core Logic

**Dosya:** `session_manager.py`

**Kritik fonksiyon:**
```python
def complete_session(user_id, course_id, completed_word_ids, db_path):
    """
    ATOMIC: Tüm progress updates tek transaction'da
    """
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("BEGIN TRANSACTION")
        
        # Get current step
        current_step = get_current_step(conn, user_id, course_id)
        
        # Update each word
        for word_id in completed_word_ids:
            update_word_progress(conn, user_id, word_id, current_step)
        
        # Increment step
        conn.execute("""
            UPDATE UserCourseProgress 
            SET current_step = current_step + 1
            WHERE user_id = ? AND course_id = ?
        """, (user_id, course_id))
        
        conn.commit()
        return {"status": "success", "new_step": current_step + 1}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
```

### Adım 4: API Endpoints

**Dosya:** `api/endpoints.py`

**3 endpoint gerekli:**

1. **POST /session/start**
   ```python
   # Empty step skip loop
   while skip_count < 200:
       items = get_new_words() + get_review_words()
       if items:
           return SessionStartResponse(items=items)
       else:
           increment_step()
           skip_count += 1
   ```

2. **POST /session/complete**
   ```python
   result = complete_session(user_id, course_id, word_ids)
   return result
   ```

3. **POST /reset**
   ```python
   DELETE FROM UserProgress WHERE user_id = ?
   DELETE FROM UserCourseProgress WHERE user_id = ? AND course_id = ?
   ```

### Adım 5: Frontend Essentials

**Single HTML file gerekli:**

```html
<script>
const API_URL = "http://localhost:8000";

// State
let sessionQueue = [];
let currentCard = null;

// Flow
async function startSession() {
    const data = await fetch(`${API_URL}/session/start`, {...});
    sessionQueue = data.items;
    renderNextCard();
}

function renderNextCard() {
    if (sessionQueue.length === 0) {
        startSession(); // Yeni session
        return;
    }
    currentCard = sessionQueue.shift();
    // Render UI...
    playAudio(currentCard.audio_en_url);
}

function handleReveal() {
    // Show turkish
    // Play turkish audio
}

async function handleComplete() {
    await fetch(`${API_URL}/session/complete`, {
        body: JSON.stringify({
            user_id: 1,
            course_id: 1,
            completed_word_ids: [currentCard.word_id]
        })
    });
    renderNextCard();
}
</script>
```

---

## 🎯 Kritik "Gotcha"lar (Dikkat Edilmesi Gerekenler)

### 1. Fibonacci vs 1-4-7-10 Karışıklığı

**YANLIŞ:**
```python
# 1-4-7-10'u review gaps'e uygulamaya çalışmak
if new_rep_count <= 3:
    next_review = current + 3  # ❌ YANLIŞ
```

**DOĞRU:**
```python
# 1-4-7-10 SADECE yeni kelime için
if (current_step - 1) % 3 == 0:
    fetch_new_word()  # ✅

# Review her zaman Fibonacci
next_review = current + fibonacci(rep_count)  # ✅
```

### 2. Review Sıralaması

**İlk deneme:** `ORDER BY repetition_count` → Yanlış sıra  
**Düzeltme:** `ORDER BY order_number DESC` → Doğru (yeni kelimeler önce)

**Neden?** Higher order_number = daha sonra öğrenilen = daha yeni = öncelikli

### 3. Empty Step Handling

**YANLIŞ:**
```python
# Boş step'te hata döndürmek
if not items:
    return {"error": "No cards"}  # ❌
```

**DOĞRU:**
```python
# Boş step'i otomatik skip et
while skip_count < 200:
    if items:
        return items
    else:
        increment_step()  # Skip
        skip_count += 1
```

### 4. Atomic Transaction

**YANLIŞ:**
```python
# Adım adım commit
update_word(word1)
conn.commit()  # ❌ Crash olursa yarım veri!
update_word(word2)
conn.commit()
```

**DOĞRU:**
```python
# Tek transaction
conn.execute("BEGIN")
update_word(word1)
update_word(word2) 
increment_step()
conn.execute("COMMIT")  # ✅ All or nothing
```

---

## 📚 Referans Dosyalar

### Okuması Zorunlu
1. `uygulama.text` - Algoritma spec (EN KRİTİK)
2. `API_CONTRACT.md` - Backend spec
3. `CSV_DATA_CONTRACT.md` - Data format

### Yardımcı Dökümanlar
4. `tanıtım.text` - Felsefe ve motivasyon
5. `ui_flow_spec.text` - UI akışı
6. `test_scenarios.md` - 31 test senaryosu

### Kod Referansları
7. `session_manager.py` - Core logic implementasyonu
8. `endpoints.py` - API implementasyonu
9. `index.html` - Frontend implementasyonu

---

## 🧪 Test Checklist

Yeniden inşa sonrası bu testleri yap:

### Backend Tests

```bash
# 1. Fibonacci doğrulaması
python3 -c "from session_manager import fibonacci; \
print([fibonacci(i) for i in range(1, 11)])"
# Expected: [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]

# 2. Database reset
sqlite3 englishbus.db "DELETE FROM UserProgress; \
DELETE FROM UserCourseProgress;"

# 3. Session start (step 1 check)
curl -X POST http://localhost:8000/session/start \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "course_id": 1}'
# Expected: current_step=1, 1 NEW word

# 4. Atomic transaction test
cd tests && python3 test_atomic_sessions.py
# Expected: All tests pass
```

### Pattern Verification

```python
# 10-step simulation
expected = "I, I, I, am, am, I, am, here, here, am, I, here"
# Run simulation (kod var test_atomic_sessions.py'de)
# Verify: System output == Expected
```

---

## 🚨 Deployment Checklist

Production'a çıkmadan önce:

- [ ] CORS: `allow_origins=["*"]` → Specific domain
- [ ] Authentication: JWT implement et
- [ ] HTTPS: SSL certificate
- [ ] Environment variables: API keys, secrets
- [ ] Database backup: Automated backup schedule
- [ ] Monitoring: Error tracking (Sentry?)
- [ ] Rate limiting: API abuse prevention
- [ ] Mobile app: Native wrapper (Capacitor/Cordova)

---

## 💡 Öğrenilen Dersler

### Teknik
1. **Spec-first development works**: API_CONTRACT.md önce yazıldı, implement sonra
2. **Atomic transactions critical**: Crash durumunda veri bütünlüğü
3. **Single file frontend viable**: Framework gerekmedi MVP için
4. **SQLite sufficient for MVP**: PostgreSQL şimdilik gerekmedi

### Süreç
1. **Test senaryoları erken yazılmalı**: Retroaktif test zor
2. **Pattern verification kritik**: Manuel test yeterli değil
3. **Documentation as you go**: Retroaktif doc yazmak uzun sürüyor
4. **Iterative debugging effective**: Fibonacci bug 3 iterasyonda çözüldü

### Ürün
1. **Minimalism works**: Özellik azlığı problem değil
2. **No gamification refreshing**: Streak yok = stress yok
3. **Audio critical**: Pasif listening öğrenmeyi güçlendiriyor
4. **Mobile access essential**: Desktop-only limitation olurdu

---

## 📞 Destek Dosyaları

Eğer bu proje kaybolursa, şu dosyaları koru:

### Kritik (Bunlar olmadan yeniden inşa zor)
- `uygulama.text` ⭐⭐⭐
- `SYSTEM_CAPABILITIES.md` ⭐⭐⭐
- `PROJECT_HISTORY.md` (bu dosya) ⭐⭐⭐
- `backend/session_manager.py` ⭐⭐
- `backend/api/endpoints.py` ⭐⭐

### Yardımcı (İşi kolaylaştırır)
- `API_CONTRACT.md` ⭐
- `CSV_DATA_CONTRACT.md` ⭐
- `test_scenarios.md` ⭐
- `index.html` ⭐

### Opsiyonel
- Test dosyaları
- Walkthrough'lar
- Fibonacci documentation

---

**Son Not:** 

Bu proje 3 günde inşa edildi. Yeniden inşa da 3 günden kısa sürebilir çünkü:
- Tüm hatalar bilinir hale geldi
- Doğru pattern'ler belgelendi
- Test senaryoları hazır

Ama en önemlisi: **Sistem felsefesi anlaşıldı**.  
Zaman değil adım, test değil güven, bitmiş değil sonsuz tekrar.

**Hazırlayan:** Antigravity AI + Emrah  
**Tarih:** 2025-12-15T02:00  
**Durum:** Checkpoint 1 - Ready for Next Phase
