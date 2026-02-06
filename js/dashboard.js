import { AppState, StateManager } from './state.js';
import { CONSTANTS } from './constants.js';
import { API } from './api.js';

export const Dashboard = {
    async init() {
        // Initial Load
        await this.loadCourses();
        this.updateData();

        // Listen for screen changes to refresh data
        window.addEventListener('screen-changed', (e) => {
            if (e.detail.screenId === 'dashboard-screen') this.updateData();
        });

        // Start Button Logic
        const startBtn = document.getElementById('btn-main-start');
        if (startBtn) {
            startBtn.onclick = () => {
                const mode = AppState.studyMode || 'words';

                if (mode === 'sentences') {
                    // Sentences don't need a specific unit, they use the course ID
                    import('./study.js').then(m => m.StudyEngine.start(null));
                } else {
                    // Words Mode: Needs Unit Logic
                    const units = AppState.units || [];
                    if (units.length > 0) {
                        // Logic: Find first unlocked unit
                        const target = units.find(u => u.status !== 'LOCKED') || units[0];
                        import('./study.js').then(m => m.StudyEngine.start(target.unit_id));
                    } else {
                        alert("Çalışılacak ünite bulunamadı.");
                    }
                }
            };
        }

        // Expose global functions for HTML onclicks
        window.switchStudyMode = (mode) => this.switchStudyMode(mode);
        window.Dashboard = this;
    },

    switchStudyMode(mode) {
        // Update State
        AppState.studyMode = mode;

        // Update UI Styles
        const btnWords = document.getElementById('btn-mode-words');
        const btnSentences = document.getElementById('btn-mode-sentences');

        // Reset classes - Simplified toggle logic
        if (mode === 'words') {
            if (btnWords) {
                btnWords.className = "flex-1 flex items-center justify-center gap-3 bg-white/60 border-2 border-brand-500 rounded-xl py-4 transition-all glass hover:bg-white shadow-sm group";
                const icon = btnWords.querySelector('div');
                if (icon) icon.className = "p-2 bg-brand-100 rounded-lg text-brand-600 group-hover:scale-110 transition-transform";
                const text = btnWords.querySelector('span:last-child');
                if (text) text.className = "text-gray-800 font-bold";
            }
            if (btnSentences) {
                btnSentences.className = "flex-1 flex items-center justify-center gap-3 bg-white/40 hover:bg-white/60 border border-white/20 rounded-xl py-4 transition-all glass hover:shadow-sm text-gray-500 hover:text-gray-700";
                const icon = btnSentences.querySelector('div');
                if (icon) icon.className = "p-2 bg-gray-100 rounded-lg text-gray-400";
                const text = btnSentences.querySelector('span:last-child');
                if (text) text.className = "font-bold";
            }
        } else {
            // Sentences Active
            if (btnSentences) {
                btnSentences.className = "flex-1 flex items-center justify-center gap-3 bg-white/60 border-2 border-brand-500 rounded-xl py-4 transition-all glass hover:bg-white shadow-sm group";
                const icon = btnSentences.querySelector('div');
                if (icon) icon.className = "p-2 bg-brand-100 rounded-lg text-brand-600 group-hover:scale-110 transition-transform";
                const text = btnSentences.querySelector('span:last-child');
                if (text) text.className = "text-gray-800 font-bold";
            }
            if (btnWords) {
                btnWords.className = "flex-1 flex items-center justify-center gap-3 bg-white/40 hover:bg-white/60 border border-white/20 rounded-xl py-4 transition-all glass hover:shadow-sm text-gray-500 hover:text-gray-700";
                const icon = btnWords.querySelector('div');
                if (icon) icon.className = "p-2 bg-gray-100 rounded-lg text-gray-400";
                const text = btnWords.querySelector('span:last-child');
                if (text) text.className = "font-bold";
            }
        }
    },

    async loadCourses() {
        try {
            const data = await API.course.list();
            const courses = data.courses || [];
            StateManager.update('allCourses', courses);

            const selSettings = document.getElementById('settings-course-select');

            // Default Course Logic
            let currentId = AppState.courseId || localStorage.getItem(CONSTANTS.LOCAL_KEYS.COURSE_ID);

            // If no course selected or valid defaults, pick first
            if (!currentId && courses.length > 0) {
                currentId = courses[0].id;
            }

            if (currentId) {
                StateManager.update('courseId', currentId);
                localStorage.setItem(CONSTANTS.LOCAL_KEYS.COURSE_ID, currentId);
            }

            // Populate Settings Dropdown
            if (selSettings) {
                selSettings.innerHTML = '';
                courses.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c.id;
                    opt.text = c.name;
                    selSettings.appendChild(opt);
                });
                if (AppState.courseId) selSettings.value = AppState.courseId;
                selSettings.onchange = () => this.handleCourseChange(selSettings);
            }

        } catch (err) {
            console.error("Courses Load Failed:", err);
            this.renderEmptyState();
        }
    },

    async updateData(forceReload = false) {
        if (!AppState.user) return; // User must be logged in

        try {
            // 1. Ensure courses are loaded
            if (!AppState.allCourses || AppState.allCourses.length === 0) {
                await this.loadCourses();
            }

            const courseId = AppState.courseId;
            if (!courseId) {
                console.warn("No active course found.");
                this.renderEmptyState();
                return;
            }

            // Update Header Name
            const course = AppState.allCourses ? AppState.allCourses.find(c => c.id == courseId) : null;
            if (course) {
                const nameEl = document.getElementById('dashboard-course-name');
                if (nameEl) nameEl.textContent = course.name;
            }

            console.log(`Fetching units for Course ${courseId}, User ${AppState.user.id}`);

            // 2. Fetch Units & Stats
            const [status, repStats] = await Promise.all([
                API.course.getUnitsStatus(courseId, AppState.user.id),
                API.course.getRepetitionStats(courseId, AppState.user.id)
            ]);

            StateManager.update('units', status.units || []);
            StateManager.update('dailyNewWords', status.daily_new_count || 0);
            StateManager.update('repStats', repStats || { new_seen: 0, mid_level: 0, mastered: 0 });

            // 3. Render
            this.render();

        } catch (err) {
            console.error("Dashboard Update Failed:", err);
            const container = document.getElementById('dashboard-units-container');
            if (container) container.innerHTML = `<div class="text-red-500 text-center p-4">Veri yüklenemedi. Bağlantınızı kontrol edin.</div>`;
        }
    },

    render() {
        this.renderUnits();
        this.renderStats();
    },

    renderUnits() {
        const grid = document.getElementById('dashboard-units-container');
        if (!grid) return;
        grid.innerHTML = '';

        const units = AppState.units || [];

        if (units.length === 0) {
            grid.innerHTML = `<div class="text-gray-400 text-center py-10">Bu kursta henüz ünite yok.</div>`;
            return;
        }

        units.forEach(unit => {
            const isLocked = unit.status === 'LOCKED';
            // Fix: Use correct properties from UnitProgressModel
            const progressPct = Math.round(unit.progress?.seen_percentage || 0);
            const totalWords = unit.progress?.total || 0;

            // Glassmorphism Card (Row Style)
            const card = document.createElement('div');
            card.className = `glass-panel p-4 flex items-center justify-between gap-4 transition-all duration-300 hover:scale-[1.01] ${isLocked ? 'opacity-60 grayscale' : 'cursor-pointer hover:bg-white/40'}`;

            if (!isLocked) {
                card.onclick = () => {
                    import('./study.js').then(m => m.StudyEngine.start(unit.unit_id));
                };
            }

            card.innerHTML = `
                <div class="flex items-center gap-4">
                    <div class="size-12 rounded-xl flex items-center justify-center ${isLocked ? 'bg-gray-200 text-gray-400' : 'bg-brand-100 text-brand-600'}">
                        <span class="material-symbols-outlined text-2xl">${isLocked ? 'lock' : 'menu_book'}</span>
                    </div>
                    <div>
                        <h3 class="font-bold text-gray-800 text-lg">${unit.name}</h3>
                        <p class="text-xs text-gray-500 font-medium">${totalWords} Kelime • ${progressPct}% Tamamlandı</p>
                    </div>
                </div>
                
                <div class="w-12 h-12 relative flex items-center justify-center">
                    ${!isLocked ? '<span class="material-symbols-outlined text-brand-500 text-2xl">play_circle</span>' : '<span class="material-symbols-outlined text-gray-400">lock</span>'}
                </div>
            `;

            grid.appendChild(card);
        });
    },

    renderEmptyState() {
        const grid = document.getElementById('dashboard-units-container');
        if (grid) grid.innerHTML = `<div class="text-gray-400 text-center py-10">Kayıtlı kurs bulunamadı.</div>`;
    },

    renderStats() {
        // Populate Bento Grid Stats IDs
        const newCount = document.getElementById('stat-new-count');

        // Populate Repetition Stats
        const stats = AppState.repStats || { new_seen: 0, mid_level: 0, mastered: 0 };

        if (newCount) newCount.textContent = stats.new_seen || 0;

        const midCount = document.getElementById('stat-mid-count');
        if (midCount) midCount.textContent = stats.mid_level || 0;

        const masterCount = document.getElementById('stat-master-count');
        if (masterCount) masterCount.textContent = stats.mastered || 0;

        // Populate Header Stats
        // Fix: Use u.progress.total instead of u.word_count
        const totalWords = (AppState.units || []).reduce((acc, u) => acc + (u.progress?.total || 0), 0);
        const statsEl = document.getElementById('dashboard-course-stats');
        if (statsEl) statsEl.textContent = `${totalWords} Kelime`;

        // Progress Bar
        // Fix: Use u.progress.seen_percentage instead of percentage
        // Also calculate average progress properly
        const unitCount = AppState.units?.length || 1;
        const totalProgress = (AppState.units || []).reduce((acc, u) => acc + (u.progress?.seen_percentage || 0), 0) / unitCount;

        const bar = document.getElementById('dashboard-progress-bar');
        const pctEl = document.getElementById('dashboard-progress-percent');

        if (bar) bar.style.width = `${Math.round(totalProgress)}%`;
        if (pctEl) pctEl.textContent = `${Math.round(totalProgress)}%`;
    },

    handleCourseChange(select) {
        const newId = parseInt(select.value);
        if (newId) {
            StateManager.update('courseId', newId);
            localStorage.setItem(CONSTANTS.LOCAL_KEYS.COURSE_ID, newId);
            this.updateData(true);
        }
    }
};
