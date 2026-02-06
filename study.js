import { API } from './api.js';
import { AppState, StateManager } from './state.js';
import { CONSTANTS } from './constants.js';
import { UI, Modal } from './ui.js';
import { Dashboard } from './dashboard.js';

export const StudyEngine = {
    async start(unitId = null) {
        console.log("🚀 Starting study session for Unit:", unitId);
        if (unitId !== null) StateManager.update('unitId', unitId);

        try {
            const mode = AppState.studyMode;
            let cards = [];
            let step = 1;

            if (mode === 'sentences') {
                const data = await API.practice.getSentences(AppState.user.user_id, AppState.courseId, 10);
                if (data.sentences && data.sentences.length > 0) {
                    cards = data.sentences.map((s, idx) => ({
                        id: 'sent_' + idx,
                        english: s,
                        turkish: "(Cümle Çevirisi)",
                        image_url: null,
                        is_sentence: true
                    }));
                } else {
                    alert("Henüz yeterli kelime öğrenilmedi.");
                    return;
                }
            } else {
                // Word Mode
                const data = await API.session.start(AppState.user.user_id, AppState.courseId, AppState.unitId);
                // Sticky Context Update
                if (data.active_unit_id) StateManager.update('unitId', data.active_unit_id);

                cards = data.items || [];
                step = data.current_step || 1;

                // Store unit progress data
                if (data.unit_progress) {
                    StateManager.update('unitProgress', data.unit_progress);
                }

                if (cards.length === 0) {
                    alert("🎉 Bu ünite için çalışılacak kart kalmadı veya kilitli!");
                    return;
                }
            }

            // Update State
            StateManager.update('cardData', cards);
            StateManager.update('currentStep', step);
            StateManager.update('currentCardIndex', 0);
            StateManager.update('isFlipped', false);
            StateManager.update('completedBatchIds', []);

            this.loadCard();
            UI.showScreen('study-screen');

            // Background update of progress bars
            // We use Dashboard logic here or duplicate? Better to reuse via Dashboard.updateData if generic
            // Or specific logic. For Phase 1 we can skip complex progress bar inside study screen or port it.

        } catch (err) {
            console.error("Start session error:", err);
            alert("Oturum başlatılamadı.");
        }
    },

    loadCard() {
        const idx = AppState.currentCardIndex;
        const card = AppState.cardData[idx];
        if (!card) return;

        StateManager.update('isFlipped', false);

        // DOM Updates
        document.getElementById('card-front-content').classList.remove('hidden');
        document.getElementById('card-front-content').classList.add('flex');
        document.getElementById('card-back-content').classList.add('hidden');
        document.getElementById('card-back-content').classList.remove('flex');

        document.getElementById('card-english').textContent = card.english;
        document.getElementById('card-english-small').textContent = card.english;
        document.getElementById('card-turkish').textContent = card.turkish;

        const imgEl = document.getElementById('card-image');
        if (card.image_url || card.imageUrl) {
            let imageUrl = card.image_url || card.imageUrl;
            // Use backend URL for assets just like audio files
            if (imageUrl.startsWith('/assets')) {
                // Encode path segments to handle Turkish characters
                imageUrl = imageUrl.split('/').map(encodeURIComponent).join('/');
            }

            imgEl.src = imageUrl;
            imgEl.classList.remove('hidden');
        } else {
            imgEl.classList.add('hidden');
        }

        // Update progress display
        this.updateProgressDisplay();

        // Audio
        setTimeout(() => this.playAudio(), 300);
    },

    updateProgressDisplay() {
        const unitProgress = AppState.unitProgress;
        if (unitProgress) {
            const newWordsEl = document.getElementById('unit-new-words');
            const progressBarEl = document.getElementById('unit-progress-bar');

            if (newWordsEl) {
                newWordsEl.textContent = unitProgress.new_words || 0;
            }

            if (progressBarEl && unitProgress.total > 0) {
                const percentage = Math.round((unitProgress.new_words / unitProgress.total) * 100);
                progressBarEl.style.width = `${percentage}%`;
            }
        }
    },

    playAudio() {
        const idx = AppState.currentCardIndex;
        const card = AppState.cardData[idx];
        if (!card) return;

        const isBack = AppState.isFlipped;
        const text = isBack ? card.turkish : card.english;
        const lang = isBack ? 'tr-TR' : 'en-US';
        const url = isBack ? card.audio_tr_url : card.audio_en_url;

        if (url) {
            let audioUrl = url;
            if (url.startsWith('/assets')) {
                audioUrl = url.split('/').map(encodeURIComponent).join('/');
            }

            new Audio(audioUrl).play().catch(() => this.playSynthesis(text, lang));
        } else {
            this.playSynthesis(text, lang);
        }
    },

    playSynthesis(text, lang) {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance(text);
            u.lang = lang;
            u.rate = 0.9;
            window.speechSynthesis.speak(u);
        }
    },

    handleAction() {
        if (!AppState.isFlipped) {
            // Flip
            StateManager.update('isFlipped', true);
            document.getElementById('card-front-content').classList.add('hidden');
            document.getElementById('card-front-content').classList.remove('flex');
            document.getElementById('card-back-content').classList.remove('hidden');
            document.getElementById('card-back-content').classList.add('flex');
            setTimeout(() => this.playAudio(), 200);
        } else {
            // Complete
            this.completeCard();
        }
    },

    completeCard() {
        const idx = AppState.currentCardIndex;
        const card = AppState.cardData[idx];
        const wordId = card.word_id || card.id;

        if (wordId) {
            AppState.completedBatchIds.push(wordId);
            StateManager.update('currentCardIndex', idx + 1);

            if (AppState.currentCardIndex < AppState.cardData.length) {
                // Next Card
                StateManager.update('currentStep', AppState.currentStep + 1);
                this.loadCard();
            } else {
                // Batch Complete
                this.completeBatch();
            }
        }
    },

    async completeBatch() {
        if (!AppState.completedBatchIds.length) {
            this.start(AppState.unitId);
            return;
        }

        try {
            const res = await API.session.complete(AppState.user.user_id, AppState.courseId, AppState.completedBatchIds);

            // Celebration Logic
            const dailyGoal = AppState.dailyGoal;
            const dailyNew = res.daily_new_count || 0;
            const lastCeleb = AppState.lastCelebratedCount;

            if (dailyGoal > 0 && dailyNew > 0 && dailyNew % dailyGoal === 0 && dailyNew > lastCeleb) {
                UI.triggerConfetti();
                setTimeout(() => Modal.show("Tebrikler!", `Bugünkü hedefi (${dailyGoal}) tamamladın!`, null, "Harika!"), 500);
                StateManager.update('lastCelebratedCount', dailyNew);
            }

            // Sync Dashboard
            await Dashboard.updateData();

            // Update progress display with latest data
            if (res.unit_progress) {
                StateManager.update('unitProgress', res.unit_progress);
                this.updateProgressDisplay();
            }

            // Smart Transition check (Simplified)
            // Ideally we check if unit is complete and move to next
            // For now, just reload unit or next logic

            this.start(AppState.unitId); // Or logic to switch unit

        } catch (err) {
            console.error("Batch fail:", err);
            alert("Kaydedilemedi!");
        }
    }
};
