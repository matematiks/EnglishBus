# GitHub Değişiklik Günlüğü

Bu dosya, hem **bekleyen (staging)** hem de **tamamlanan (deployed)** değişiklikleri takip etmek için kullanılır.

**İş Akışı:**
1.  Yapılan her değişiklik **"Bekleyenler"** listesine eklenir.
2.  "GitHub'a Yükle" komutu verildiğinde:
    - Bu maddeler commit mesajı olur.
    - Kodlar GitHub'a gönderilir (push).
    - Maddeler **"Geçmiş Gönderimler"** altına taşınır (SİLİNMEZ).

## 🟢 Bekleyen Değişiklikler (Staging)

*(Şu an bekleyen değişiklik yok)*

> [!TIP]
> **Sunucu Disk Temizliği:** `.venv` klasörü çok yer kaplıyor (237MB). `pip install --no-cache-dir` ile yeniden kurulabilir.

---

## 📜 Geçmiş Push Kayıtları

### [Tarih: 07.02.2026 - 22:49] - v2.4.5 (Deployment Stable)
- 🆕 **New:** `[requirements_minimal.txt]` Sunucu için hafifletilmiş (pandas/numpy içermeyen) gereksinim dosyası.
- 🆕 **New:** `[scripts/cleanup_server.py]` Sunucuda gereksiz dosyaları (yedekler, cache vb.) temizleyen script.
- 🆕 **New:** `[scripts/reimport_minimal.py]` Sunucuda veritabanını güncellemek için (pandas gerektirmeyen) hafif import scripti.
- 🆕 **New:** `[scripts/diagnose_server.py]` Sunucuda veritabanı yollarını ve içeriğini kontrol eden script.
- ✅ **Fix:** Sunucu sanal ortamı (`.venv`) Python 3.10 ile yeniden oluşturuldu.
- ✅ **Fix:** `requirements_minimal.txt` doğrulandı (tüm gerekli paketler mevcut).
- ✅ **Docs:** Manuel dağıtım ve disk temizliği süreçleri doğrulandı.

### [Tarih: 07.02.2026 - 20:36] - v2.4.3 (Admin & Settings Fixes)

---

- �🛠 **Fix:** `[js/settings.js]` "Sıfırlanacak Kurs" listesi boş geliyordu. Fonksiyon bağımsız çalışacak şekilde güncellendi.
- 🗑 **Cleanup:** `[index.html]` Profil sekmesindeki sahte veriler (Liderlik, 45dk odaklanma vb.) temizlendi.
- 🗑 **Cleanup:** `[index.html, js/settings.js]` "Veri Yedeğini İndir" butonu ve fonksiyonları kaldırıldı.
- 🗑 **Cleanup:** `[index.html, js/settings.js]` "Yazı Boyutu" ayarı ve fonksiyonları kaldırıldı.
- 🛠 **Fix:** `[admin.html]` Mesaj gönderme servisi adresi düzeltildi (`/admin/messages/send`).
- 🔐 **Security:** Admin şifresi `123456` olarak güncellendi.

### [Tarih: 07.02.2026 - 20:00] - v2.4.2 (Deploy Edildi)
- ✅ **Fix:** Ses ikonu kelime kartlarından kaldırıldı (UI cleanup).
- ✅ **Fix:** Mobil alt menü (bottom nav) giriş ekranında gizlendi.
- ✅ **Feat:** Üniteler 50'şer kelimelik parçalara bölündü (reimport_all.py güncellendi).
