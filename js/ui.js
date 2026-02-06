export const UI = {
    showScreen(screenId) {
        // Hide all elements with 'screen' class
        document.querySelectorAll('.screen').forEach(el => el.classList.add('hidden'));

        // Show the target screen
        const target = document.getElementById(screenId);
        if (target) {
            target.classList.remove('hidden');

            // If we are showing the Settings screen, load current settings
            if (screenId === 'settings-screen' && typeof loadSettings === 'function') {
                loadSettings();
            }
            window.scrollTo(0, 0);

            // Update Bottom Nav Active State
            this.updateBottomNav(screenId);

            // Dispatch Event for Logic Components
            window.dispatchEvent(new CustomEvent('screen-changed', {
                detail: { screenId }
            }));
        } else {
            console.error("❌ ShowScreen Error: Element not found ->", screenId);
        }
    },

    updateBottomNav(screenId) {
        const nav = document.getElementById('mobile-bottom-nav');
        if (!nav) return;

        // Reset all active states
        nav.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

        // Determine which button corresponds to this screen
        // Maps screen ID to the button index or selector
        const buttons = nav.querySelectorAll('.nav-item');

        if (screenId === 'dashboard-screen') {
            buttons[0]?.classList.add('active'); // Home
        } else if (screenId === 'settings-screen') {
            buttons[2]?.classList.add('active'); // Profile (Settings)
        }
        // Play button (index 1) doesn't have a persistent screen state usually, or maps to study-screen?
        // study-screen usually hides the nav or is an overlay.
    },

    updateGoalDisplay(val) {
        // Modal Input
        const input = document.getElementById('daily-goal-input');
        if (input && input.value != val) input.value = val;

        // On-page displays
        const displays = document.querySelectorAll('#goal-display, #onpage-goal-display');
        displays.forEach(display => {
            if (val == 0) {
                display.textContent = 'Hedef Yok';
                display.className = display.id === 'onpage-goal-display'
                    ? 'text-sm font-black text-gray-500 bg-gray-100 px-2 py-1 rounded-lg'
                    : 'text-sm font-bold text-gray-500 bg-gray-100 px-3 py-1 rounded-full';
            } else {
                if (display.id === 'onpage-goal-display') {
                    // This often needs context (current / total), handled by dashboard logic mostly.
                    // But for pure goal update:
                    display.textContent = `${val} Kelime Hedefi`;
                } else {
                    display.textContent = `${val} Kelime`;
                    display.className = 'text-sm font-bold text-blue-600 bg-blue-50 px-3 py-1 rounded-full';
                }
            }
        });
    },

    triggerConfetti() {
        if (typeof confetti === 'undefined') return;

        const duration = 3000;
        const animationEnd = Date.now() + duration;
        const randomInRange = (min, max) => Math.random() * (max - min) + min;

        const interval = setInterval(() => {
            const timeLeft = animationEnd - Date.now();
            if (timeLeft <= 0) return clearInterval(interval);

            const particleCount = 50 * (timeLeft / duration);
            confetti({
                particleCount,
                startVelocity: 30,
                spread: 360,
                ticks: 60,
                origin: { x: randomInRange(0.1, 0.9), y: Math.random() - 0.2 },
                colors: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6']
            });
        }, 250);
    },

    showLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.classList.remove('hidden');
    },

    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.classList.add('hidden');
    }
};

export const Modal = {
    el: null,
    currentCallback: null,

    init() {
        this.el = document.getElementById('confirmation-modal');
    },

    show(title, message, onConfirm, confirmText = "Evet", confirmColor = "bg-red-600 hover:bg-red-700") {
        if (!this.el) this.init();
        if (!this.el) return alert(message);

        document.getElementById('modal-title').textContent = title;
        document.getElementById('modal-message').textContent = message;

        const btn = document.getElementById('btn-modal-confirm');
        if (btn) {
            btn.className = `flex-1 py-3 text-white font-bold rounded-xl ${confirmColor}`;
            btn.textContent = confirmText;

            // Remove old listener if any to prevent stacking
            // Ideally use a 'once' listener or reset
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);

            newBtn.addEventListener('click', () => {
                if (onConfirm) onConfirm();
                this.hide();
            });
        }

        this.el.classList.remove('hidden');
    },

    hide() {
        if (this.el) this.el.classList.add('hidden');
    }
};
