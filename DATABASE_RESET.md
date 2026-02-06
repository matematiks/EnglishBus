# EnglishBus - Database Reset Guide

## 🔄 Kullanıcı İlerlemesini Sıfırlama

### Tek Komutla Sıfırlama

```bash
sqlite3 englishbus.db "DELETE FROM UserProgress WHERE user_id = 1; DELETE FROM UserCourseProgress WHERE user_id = 1;"
```

### Adım Adım

1. **Projeye dizinine git:**
   ```bash
   cd /Users/emrah/Documents/Projeler/EnglishBus
   ```

2. **İlerlemeyi sıfırla:**
   ```bash
   sqlite3 englishbus.db "DELETE FROM UserProgress WHERE user_id = 1; DELETE FROM UserCourseProgress WHERE user_id = 1;"
   ```

3. **Doğrula:**
   ```bash
   sqlite3 englishbus.db "SELECT COUNT(*) FROM UserProgress WHERE user_id = 1;"
   ```
   Sonuç: `0` olmalı

4. **Tarayıcıyı yenile:**
   - `index.html` sayfasını yenile (F5)
   - Step 1'den başlamalı

## 🔧 Tüm Kullanıcıları Sıfırlama (Geliştirme)

```bash
sqlite3 englishbus.db "DELETE FROM UserProgress; DELETE FROM UserCourseProgress;"
```

## 📊 İlerleme Durumunu Kontrol Etme

```bash
sqlite3 englishbus.db "SELECT * FROM UserCourseProgress WHERE user_id = 1;"
```

## ⚠️ Dikkat

- Kurslar ve kelimeler silinmez (sadece kullanıcı ilerlemesi)
- `Words`, `Units`, `Courses` tabloları etkilenmez
- Sadece progress kayıtları silinir

## 🚀 Hızlı Reset Script

Aşağıdaki komutu bir alias olarak kaydedebilirsin:

```bash
alias resetbus="cd /Users/emrah/Documents/Projeler/EnglishBus && sqlite3 englishbus.db 'DELETE FROM UserProgress WHERE user_id = 1; DELETE FROM UserCourseProgress WHERE user_id = 1;' && echo 'Progress reset!'"
```

Sonra terminalde sadece `resetbus` yazarak sıfırlayabilirsin.
