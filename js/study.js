import { API } from './api.js';
import { AppState, StateManager } from './state.js';
import { CONSTANTS } from './constants.js';
import { UI, Modal } from './ui.js';
import { Dashboard } from './dashboard.js';

export const StudyEngine = {
    async start(unitId = null) {
        console.log("🚀 Starting study session...", unitId);
        UI.showLoading(); // Show loader immediately

        if (unitId !== null) StateManager.update('unitId', unitId);

        // Ensure user
        if (!AppState.user) {
            const storedUser = localStorage.getItem(CONSTANTS.LOCAL_KEYS.USER);
            if (storedUser) StateManager.update('user', JSON.parse(storedUser));
            else {
                UI.hideLoading(); // Hide if Redirecting
                UI.showScreen('login-screen');
                return;
            }
        }

        try {
            const mode = AppState.studyMode || 'words';
            let cards = [];
            let currentStep = null;

            // 1. Fetch Data
            if (mode === 'sentences') {
                const res = await API.practice.getSentences(
                    AppState.user.id,
                    AppState.courseId || localStorage.getItem(CONSTANTS.LOCAL_KEYS.COURSE_ID),
                    10
                );

                if (res.status === 'insufficient_vocabulary') {
                    UI.hideLoading();
                    Modal.show(
                        'Yetersiz Kelime',
                        'Cümle kurabilmek için yeterli kelime öğrenmediniz. Lütfen önce kelime çalışın.',
                        () => { UI.showScreen('dashboard-screen'); },
                        'Anladım',
                        'bg-yellow-600 hover:bg-yellow-700'
                    );
                    return;
                }
                cards = res.sentences || [];
            } else {
                // WORDS
                // Use API.session.start to match Remote Backend ("correct" logic)
                const res = await API.session.start(
                    AppState.user.id,
                    AppState.courseId || localStorage.getItem(CONSTANTS.LOCAL_KEYS.COURSE_ID),
                    unitId
                );
                currentStep = res.current_step;
                cards = res.items || [];

                if (res.active_unit_id) StateManager.update('activeUnitId', res.active_unit_id);
                // Note: Remote endpoint might put unit_progress in top level or inside session
                if (res.unit_progress) StateManager.update('unitProgress', res.unit_progress);
            }

            // 2. Empty Check
            if (!cards || cards.length === 0) {
                UI.hideLoading();
                // If pure empty, maybe show modal. But in infinite flow we might restart?
                // For now use Modal as fallback.
                if (mode === 'sentences') {
                    Modal.show(
                        'Henüz Hazır Değil',
                        'Henüz yeterli kelime yok lütfen kelime çalışın',
                        () => { UI.showScreen('dashboard-screen'); },
                        'Tamam',
                        'bg-yellow-600 hover:bg-yellow-700'
                    );
                } else {
                    // Word Mode: Infinite flow implies this should only happen if course is empty/broken
                    Modal.show(
                        'İçerik Bulunamadı',
                        'Bu kursta çalışılacak kelime bulunamadı veya bir hata oluştu.',
                        () => { UI.showScreen('dashboard-screen'); },
                        'Ana Menü',
                        'bg-gray-600 hover:bg-gray-700'
                    );
                }
                return;
            }

            // 3. Init State for Batch
            StateManager.update('sessionCards', cards);
            StateManager.update('sessionCompletedIds', []); // Reset batch
            StateManager.update('currentIndex', 0);
            if (currentStep) StateManager.update('currentStep', currentStep);

            UI.hideLoading(); // Hide before showing screen
            UI.showScreen('study-screen');
            this.showCard(0);

        } catch (err) {
            console.error("Study Start Error:", err);
            UI.hideLoading();
            alert("Oturum başlatılamadı: " + (err.message || "Bilinmeyen hata"));
            UI.showScreen('dashboard-screen');
        }
    },

    showCard(index) {
        const cards = AppState.sessionCards;
        // End of Batch Check
        if (!cards || index >= cards.length) {
            this.finishSession();
            return;
        }

        StateManager.update('currentIndex', index);
        const card = cards[index];

        // --- RENDER UI (Matching index.html IDs) ---

        // Image
        const imgEl = document.getElementById('card-image');
        if (imgEl) {
            const showImages = AppState.settings?.show_images !== false;
            const hasImage = !!card.image_url;
            imgEl.style.display = (hasImage && showImages) ? 'block' : 'none';
            if (hasImage) imgEl.src = card.image_url;
        }

        // Texts
        const mainText = document.getElementById('card-main-text');
        if (mainText) {
            mainText.textContent = card.english || card.target;
            mainText.classList.remove('text-brand-600', 'text-2xl', 'text-gray-800');
            mainText.classList.add('text-gray-800', 'text-4xl');
        }

        const topText = document.getElementById('card-top-text');
        if (topText) {
            // User Request: Remove "WORD"/"SENTENCE" label. Keep it clean.
            topText.textContent = "";
            topText.classList.add('opacity-0');
        }

        const subText = document.getElementById('card-sub-text');
        if (subText) {
            subText.textContent = card.turkish || card.native;
            subText.classList.add('hidden');
        }

        // Action Button Reset
        const actionBtn = document.getElementById('card-action-btn');
        if (actionBtn) {
            actionBtn.style.pointerEvents = 'auto';
            actionBtn.className = 'w-full py-4 rounded-xl font-black text-white shadow-lg transition-transform active:scale-95 flex items-center justify-center gap-2 bg-gray-900 hover:bg-black';
            actionBtn.innerHTML = '<span>GÖSTER</span> <span class="material-symbols-outlined">visibility</span>';
            actionBtn.onclick = () => this.revealAnswer(card, index);
        }

        // Auto Play
        if (AppState.settings?.auto_play) {
            const txt = card.english || card.target;
            const url = card.audio_en_url || card.audio_url;
            if (txt) this.playAudio(txt, url);
        }

        this.updateProgressDisplay();
    },

    revealAnswer(card, index) {
        // UI Updates for Reveal
        const mainText = document.getElementById('card-main-text');
        const topText = document.getElementById('card-top-text');

        if (topText) {
            topText.textContent = card.english || card.target;
            topText.classList.remove('opacity-0');
        }

        if (mainText) {
            mainText.textContent = card.turkish || card.native;
            mainText.classList.remove('text-gray-800', 'text-4xl');
            mainText.classList.add('text-brand-600', 'text-3xl');
        }

        // Play Turkish Audio (Auto)
        if (AppState.settings?.auto_play) {
            const trTxt = card.turkish || card.native;
            const trUrl = card.audio_tr_url;
            // Delay slightly to allow UI transition
            setTimeout(() => {
                if (trTxt) this.playAudio(trTxt, trUrl, 'tr-TR');
            }, 300);
        }

        // Button -> Complete
        const actionBtn = document.getElementById('card-action-btn');
        if (actionBtn) {
            actionBtn.classList.remove('bg-gray-900', 'hover:bg-black');
            actionBtn.classList.add('bg-green-500', 'hover:bg-green-600');
            actionBtn.innerHTML = '<span>TAMAMLADIM</span> <span class="material-symbols-outlined">check_circle</span>';
            actionBtn.onclick = () => this.handleCompleted(card, index);
        }
    },

    handleCompleted(card, index) {
        // --- BATCH LOGIC (From Solid Ref) ---
        // 1. Accumulate ID
        if (!AppState.sessionCompletedIds) AppState.sessionCompletedIds = [];
        AppState.sessionCompletedIds.push(card.word_id);

        // 2. Next Card
        // No per-card API call. Just move on.
        this.showCard(index + 1);
    },

    async finishSession() {
        // --- BATCH SUBMIT (From Solid Ref) ---
        // 1. Loading UI (Button only)
        const actionBtn = document.getElementById('card-action-btn');
        if (actionBtn) {
            actionBtn.style.pointerEvents = 'none';
            actionBtn.innerHTML = '<span class="material-symbols-outlined animate-spin text-white">sync</span>';
            actionBtn.classList.add('bg-gray-400', 'cursor-wait');
        }

        const completed = AppState.sessionCompletedIds || [];

        try {
            if (!completed.length) {
                // If nothing completed, just restart? or Exit?
                console.warn("Empty batch?");
                await this.start(null);
                return;
            }

            // 2. API Call (Bulk)
            if (!AppState.studyMode || AppState.studyMode === 'words') {
                const res = await API.session.complete(
                    AppState.user.id,
                    AppState.courseId,
                    completed
                );

                // Update Logic from Solid Ref
                if (res.unit_progress) {
                    StateManager.update('unitProgress', res.unit_progress);
                    this.updateProgressDisplay();
                }
            }

            // 3. Reset & Restart (Infinite Flow)
            StateManager.update('sessionCards', []);
            StateManager.update('sessionCompletedIds', []);

            await this.start(AppState.unitId);

        } catch (err) {
            console.error("Batch Complete Error:", err);
            alert("Sistem Hatası: " + err.message);
            // On error, better to exit or retry? Solid ref says alert.
            UI.showScreen('dashboard-screen');
        }
    },

    updateProgressDisplay() {
        const unitProgress = AppState.unitProgress;
        const bar = document.getElementById('unit-progress-bar');
        const text = document.getElementById('unit-new-words');

        if (unitProgress) {
            if (bar && unitProgress.total > 0) {
                // Global Unit Progress
                const percentage = Math.round((unitProgress.new_words / unitProgress.total) * 100);
                bar.style.width = `${percentage}%`;
            }
            if (text) {
                // Total words learned in unit
                text.textContent = unitProgress.new_words || 0;
            }
        }
    },

    playAudio(text, url, lang = 'en-US') {
        const speed = AppState.settings?.audio_speed || 1.0;
        if (url) {
            const audio = new Audio(url);
            audio.playbackRate = speed;
            audio.play().catch(() => this.speakTTS(text, lang));
        } else {
            this.speakTTS(text, lang);
        }
    },

    speakTTS(text, lang) {
        if (!window.speechSynthesis) return;
        const speed = AppState.settings?.audio_speed || 1.0;
        window.speechSynthesis.cancel();
        const ut = new SpeechSynthesisUtterance(text);
        ut.lang = lang;
        ut.rate = speed;
        window.speechSynthesis.speak(ut);
    }
};

// Global Exposure for HTML
window.playCardAudio = () => {
    const cards = AppState.sessionCards;
    const idx = AppState.currentIndex || 0;
    if (cards && cards[idx]) {
        const c = cards[idx];
        StudyEngine.playAudio(c.english || c.target, c.audio_en_url || c.audio_url);
    }
};
window.exitStudy = () => UI.showScreen('dashboard-screen');
