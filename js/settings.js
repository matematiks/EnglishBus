import { API } from './api.js';
import { CONSTANTS } from './constants.js';
import { StateManager } from './state.js';
import { UI } from './ui.js';

export const SettingsManager = {
    state: {
        theme: 'light',
        color_theme: 'purple',
        audio_speed: 1.0,
        auto_play: true,
        show_images: true,
        daily_goal: 10,
        active_course_id: null,
        avatar: '👤'
    },

    // Color Palettes (RGB strings for Tailwind --color-brand-500)
    colors: {
        purple: { brand: '153 0 240', accent: '249 0 191' },
        ocean: { brand: '14 165 233', accent: '56 189 248' },
        sunset: { brand: '244 63 94', accent: '251 113 133' },
        forest: { brand: '16 185 129', accent: '52 211 153' }
    },

    // Course Descriptions
    courseDescriptions: {
        1: "Rastgele kelime listelerini unutun. Dilin belkemiğini oluşturan en hayati 322 kelimeyle, ezberlemeden, doğal bir akışla konuşmaya başlayın. Bebekçe yok, karmaşa yok; sadece saf iletişim var.",
        // Add more defaults if needed or fetch from server later
    },

    init() {
        console.log("⚙️ Settings Manager Initializing...");
        this.loadLocal();
        this.bindUI();
        this.populateCourses(); // Added: Load courses immediately
        this.fetchFromServer(); // Async
        this.applyAll();
        this.checkPermissions();
    },

    loadLocal() {
        const userId = localStorage.getItem(CONSTANTS.LOCAL_KEYS.USER_ID) || 1;
        const key = `englishbus_settings_${userId}`;
        const stored = localStorage.getItem(key);
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                this.state = { ...this.state, ...parsed };
            } catch (e) {
                console.error("Settings parse error", e);
            }
        }
        // Sync to AppState
        StateManager.update('settings', this.state);
    },

    saveLocal() {
        const userId = localStorage.getItem(CONSTANTS.LOCAL_KEYS.USER_ID) || 1;
        const key = `englishbus_settings_${userId}`;
        localStorage.setItem(key, JSON.stringify(this.state));
        StateManager.update('settings', this.state);
    },

    async fetchFromServer() {
        try {
            // JWT token already contains user ID, no need for query parameter
            const data = await API.request('/user/settings');
            if (data) {
                this.state = { ...this.state, ...data };
                this.saveLocal();
                this.applyAll();
                this.populateCourses();
            }
        } catch (e) { console.error("Sync failed", e); }
    },

    applyAll() {
        this.applyTheme();
        this.applyColorTheme();
        this.applyAvatar();
        this.bindUI(); // Re-sync inputs to state
    },

    // === THEME ===
    setTheme(mode) {
        this.state.theme = mode;
        this.saveLocal();
        this.applyTheme();
    },

    applyTheme() {
        const html = document.documentElement;
        const mode = this.state.theme;

        if (mode === 'dark') {
            html.classList.add('dark');
        } else {
            html.classList.remove('dark');
        }

        const toggle = document.getElementById('settings-dark-mode');
        if (toggle) {
            toggle.checked = (mode === 'dark');
        }
    },

    // === COLORS ===
    setColorTheme(colorName) {
        if (!this.colors[colorName]) return;
        this.state.color_theme = colorName;
        this.saveLocal();
        this.applyColorTheme();
    },

    applyColorTheme() {
        const colorName = this.state.color_theme || 'purple';
        const palette = this.colors[colorName];
        if (!palette) return;

        const root = document.documentElement;
        root.style.setProperty('--color-brand-500', palette.brand);

        // Update Active State on Buttons
        ['purple', 'ocean', 'sunset', 'forest'].forEach(c => {
            const btn = document.getElementById(`color-btn-${c}`);
            if (btn) {
                if (c === colorName) {
                    btn.classList.add('border-brand-500', 'scale-105', 'shadow-lg', 'ring-1', 'ring-brand-200');
                    btn.classList.remove('border-transparent', 'hover:border-' + c + '-300');
                } else {
                    btn.classList.remove('border-brand-500', 'scale-105', 'shadow-lg', 'ring-1', 'ring-brand-200');
                    btn.classList.add('border-transparent');
                }
            }
        });
    },



    // === AVATAR ===
    avatars: ['👦', '👧', '👨', '👩', '👱', '👱‍♀️', '👴', '👵', '🦁', '🐯', '🐼', '🐨', '🐸', '🐙', '🦄', '🤖', '👽', '👻', '💩', '🚀'],

    openAvatarSelection() {
        const modal = document.getElementById('avatar-modal');
        const grid = document.getElementById('avatar-grid');
        if (!modal || !grid) return;

        grid.innerHTML = '';
        this.avatars.forEach(av => {
            const btn = document.createElement('button');
            btn.className = 'text-2xl p-2 hover:bg-gray-100 rounded-xl transition-colors';
            btn.textContent = av;
            btn.onclick = () => {
                this.setAvatar(av);
                modal.classList.add('hidden');
            };
            grid.appendChild(btn);
        });

        modal.classList.remove('hidden');
    },

    setAvatar(avatarStr) {
        this.state.avatar = avatarStr;
        this.saveLocal();
        this.applyAvatar();
        // Sync to server here ideally
    },

    applyAvatar() {
        const av = this.state.avatar || '👤';
        const display = document.getElementById('settings-avatar-display');
        const preview = document.getElementById('avatar-preview'); // Support Photovv preview

        if (display) display.textContent = av;
        if (preview) {
            preview.innerHTML = `<span class="text-3xl">${av}</span>`;
        }

        // Also update the dashboard/header avatar if possible
        const headerDisplay = document.getElementById('user-initial');
        if (headerDisplay) headerDisplay.textContent = av;
    },


    // === COURSES ===
    async populateCourses() {
        const select = document.getElementById('settings-course-select');
        const resetSelect = document.getElementById('reset-course-select'); // Photovv Reset Select

        // If neither exists, we might still want to fetch for internal state, but typically we return
        if (!select && !resetSelect) return;

        try {
            const data = await API.request('/courses');
            const courses = data.courses || [];

            // Populate Main Settings Select
            if (select) {
                select.innerHTML = '';
                courses.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c.id;
                    opt.textContent = c.name;
                    select.appendChild(opt);
                });
                if (this.state.active_course_id) {
                    select.value = this.state.active_course_id;
                    this.updateCourseDescription(this.state.active_course_id); // Initial load
                }
            }

            // Populate Reset Course Select (Danger Zone)
            if (resetSelect) {
                resetSelect.innerHTML = '<option value="">-- Kurs Seçin --</option>';
                courses.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c.id;
                    opt.textContent = c.name;
                    resetSelect.appendChild(opt);
                });
                // Add change listener inline or via binding
                resetSelect.onchange = (e) => this.handleResetCourseChange(e.target);
            }

        } catch (e) { console.error("Course fetch failed", e); }
    },

    // === BINDING ===
    bindUI() {
        const bindings = [
            { id: 'settings-auto-audio', key: 'auto_play', type: 'checkbox' },
            { id: 'settings-show-images', key: 'show_images', type: 'checkbox' },
            {
                id: 'settings-dark-mode', key: 'theme', type: 'checkbox',
                cb: (v) => this.setTheme(v ? 'dark' : 'light')
            },
            {
                id: 'settings-audio-speed', key: 'audio_speed', type: 'range',
                cb: (v) => document.getElementById('settings-speed-val').textContent = v + 'x'
            },
            {
                id: 'settings-daily-goal', key: 'daily_goal', type: 'range',
                cb: (v) => document.getElementById('goal-display').textContent = v + ' Kelime'
            }
        ];

        bindings.forEach(bind => {
            const el = document.getElementById(bind.id);
            if (!el) return;

            // Set Initial
            if (bind.type === 'checkbox') {
                if (bind.key === 'theme') el.checked = this.state.theme === 'dark';
                else el.checked = this.state[bind.key];
            } else {
                el.value = this.state[bind.key];
            }

            // Listeners logic to avoid duplicates is tricky in vanilla without cleanup.
            // Simplified: direct onclick/onchange overwrites
            el.onchange = (e) => {
                const val = bind.type === 'checkbox' ? e.target.checked : parseFloat(e.target.value);

                if (bind.key !== 'theme') { // Theme handled by cb
                    this.state[bind.key] = val;
                    this.saveLocal();
                }

                if (bind.cb) bind.cb(val);
                else this.applyAll();
            };

            if (bind.type === 'range') {
                el.oninput = (e) => {
                    const val = e.target.value; // visual update only
                    if (bind.id === 'settings-audio-speed') document.getElementById('settings-speed-val').textContent = val + 'x';
                    if (bind.id === 'settings-daily-goal') document.getElementById('goal-display').textContent = val + ' Kelime';
                };
            }
        });

        const courseSelect = document.getElementById('settings-course-select');
        if (courseSelect) {
            courseSelect.onchange = (e) => {
                this.state.active_course_id = parseInt(e.target.value);
                this.saveLocal();
                this.updateCourseDescription(this.state.active_course_id); // Update text immediately
                if (confirm("Kurs değiştirildi. Sayfanın yenilenmesi gerekiyor.")) location.reload();
            };
        }

        // Admin Button Logic
        this.checkPermissions();
    },

    updateUI() {
        this.bindUI(); // Refresh state into DOM
    },

    // === ACTIONS ===


    toggleDangerZone(event) {
        if (event) event.stopPropagation();
        const content = document.getElementById('danger-zone-content');
        const icon = document.getElementById('danger-zone-icon');
        if (content) content.classList.toggle('hidden');
        if (icon) icon.classList.toggle('rotate-180'); // Optional rotation if FA icon supported
    },

    toggleEducationZone() {
        const content = document.getElementById('education-zone-content');
        const icon = document.getElementById('education-zone-icon');
        if (content) content.classList.toggle('hidden');
        if (icon) icon.classList.toggle('rotate-180');
    },

    handleResetCourseChange(select) {
        const btn = document.getElementById('reset-course-btn');
        if (btn) btn.disabled = !select.value;
    },

    showResetConfirmation() {
        // Called by the new UI button
        const select = document.getElementById('reset-course-select');
        if (select && select.value) {
            this.pendingResetCourseId = select.value;
            this.resetProgress(); // Reuse the password modal flow
        } else {
            // Fallback if no select (e.g. old UI?) or empty
            alert("Lütfen bir kurs seçin.");
        }
    },

    async resetProgress() {
        const modal = document.getElementById('reset-modal');
        const input = document.getElementById('reset-password-input');

        // If pendingResetCourseId is not set (e.g. old button clicked), default to active
        if (!this.pendingResetCourseId && this.state.active_course_id) {
            this.pendingResetCourseId = this.state.active_course_id;
        }

        if (modal) {
            modal.classList.remove('hidden');
            if (input) input.value = ''; // clear previous dict
            if (input) input.focus();
        }
    },

    async confirmSecureReset() {
        const password = document.getElementById('reset-password-input').value;
        if (!password) {
            alert("Lütfen şifrenizi girin.");
            return;
        }

        const targetCourseId = this.pendingResetCourseId || this.state.active_course_id;

        if (!targetCourseId) {
            alert("Sıfırlanacak kurs seçili değil.");
            return;
        }

        const confirmBtn = document.querySelector('#reset-modal button.bg-red-500');
        const originalText = confirmBtn ? confirmBtn.innerHTML : 'Sıfırla';
        if (confirmBtn) {
            confirmBtn.disabled = true;
            confirmBtn.innerHTML = '<span class="material-symbols-outlined animate-spin">refresh</span> İşleniyor...';
        }

        try {
            await API.request('/reset', 'POST', {
                course_id: targetCourseId,
                password: password
            });
            alert("✅ İlerleme başarıyla sıfırlandı.");
            location.reload();
        } catch (e) {
            alert("🔴 Hata: " + (e.error || e.message || "Bilinmeyen hata"));
            if (confirmBtn) {
                confirmBtn.disabled = false;
                confirmBtn.innerHTML = originalText;
            }
        }
    },

    checkPermissions() {
        const adminBtn = document.getElementById('settings-btn-admin');
        const role = localStorage.getItem('role'); // Assumed usage
        if (adminBtn) {
            // Simple role check logic, or just enabling it for now as requested by user often
            // actually user wants to know if things work. 
            // I'll leave it hidden by default unless logic shows it.
            // For now, let's just make it clickable if it IS shown.
            adminBtn.onclick = () => window.location.href = '/admin.html';
        }
    },
    updateCourseDescription(courseId) {
        const descEl = document.getElementById('course-description-text');
        if (!descEl) return;

        const text = this.courseDescriptions[courseId];

        if (text) {
            descEl.textContent = text;
            descEl.classList.remove('hidden');
        } else {
            descEl.textContent = '';
            descEl.classList.add('hidden');
        }
    }
};

// Expose to window for HTML inline events
if (typeof window !== 'undefined') {
    window.SettingsManager = SettingsManager;
    // Expose utility functions used in HTML
    window.toggleDangerZone = () => SettingsManager.toggleDangerZone();
    window.toggleEducationZone = () => SettingsManager.toggleEducationZone();
    window.showResetConfirmation = () => SettingsManager.showResetConfirmation();
}

// Initialize Settings
SettingsManager.init();
// Expose functions for HTML inline handlers (needed because this is a module)
window.SettingsManager = SettingsManager;
window.toggleDangerZone = (e) => SettingsManager.toggleDangerZone(e);
window.showResetConfirmation = () => SettingsManager.showResetConfirmation();
window.handleResetCourseChange = (el) => SettingsManager.handleResetCourseChange(el);
