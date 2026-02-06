# Çalışma Modülü ve SRS Entegrasyonu (Walkthrough)

## Yapılan Değişiklikler

### 1. Backend (API ve Mantık)
*   **Yeni Endpointler**:
    *   `GET /api/study/session`: Oturum verilerini getirmek için eklendi.
    *   `POST /api/study/record`: Kart bazlı (anlık) ilerleme kaydı için eklendi.
*   **Oturum Yöneticisi (`session_manager.py`)**:
    *   GitHub stili `update_word_progress` fonksiyonu güncellendi. Artık `quality` (0-5) parametresini kabul ediyor.
    *   **SRS Mantığı**:
        *   **0-2 (Fail/Tekrar)**: Kelime "reset"lenir (Rep=1, Next Step=+1).
        *   **3 (Zor)**: ilerleme duraksar (Rep=Same, Next Step=+1).
        *   **4-5 (Kolay/İyi)**: İlerleme devam eder (Rep+1, Next Step=Fibonacci).

### 2. Frontend (`js/study.js` ve `js/api.js`)
*   **Gerçek API Bağlantısı**: Mock veri yerine `API.study.getSession` ve `API.study.record` kullanılıyor.
*   **Yeni Buton**: "Tekrar" butonu eklendi.
*   **Eşleşme**:
    *   **Kolay**: Quality 5 (İlerletir)
    *   **Zor**: Quality 3 (Duraksatır/Pekiştirir)
    *   **Tekrar**: Quality 1 (Sıfırlar)
*   **Anlık Kayıt**: Kullanıcı butona bastığı anda `API.study.record` arka planda çağrılır.

### 3. Güvenlik
*   `js/study.js` dosyasının yedeği `yedekler/yedek_study.js` olarak alındı.

## Nasıl Test Edilir?
1.  Dashboard'dan bir üniteye tıklayın veya "Çalışmaya Başla" deyin (Tarayıcı konsolunda "🚀 Starting Real-Time Session..." görmelisiniz).
2.  Kartları cevaplayın.
3.  Network tabında `POST /api/study/record` isteklerini gözlemleyin.
4.  Oturum bitince "Tebrikler" ekranını ve Adım (Step) artışını doğrulayın.
