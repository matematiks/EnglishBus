export const Shortcuts = {
    init() {
        document.addEventListener('keydown', (e) => this.handleKey(e));
        console.log("⌨️ Shortcuts Initialized");
    },

    handleKey(e) {
        // Ignore if focus is on input
        if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) return;

        const studyScreen = document.getElementById('study-screen');
        const isStudyActive = studyScreen && !studyScreen.classList.contains('hidden');

        if (isStudyActive) {
            // SPACE: Replay Audio
            if (e.code === 'Space') {
                e.preventDefault(); // Prevent scroll
                if (window.playCardAudio) window.playCardAudio();
            }

            // ENTER: Action (Show / Next)
            if (e.code === 'Enter') {
                e.preventDefault();
                if (window.handleCardAction) window.handleCardAction();
            }

            // ESC: Exit
            if (e.code === 'Escape') {
                if (window.exitStudy) window.exitStudy();
            }
        }
    }
};

// Global expose for ease if needed, but app.js import is better
window.Shortcuts = Shortcuts;
