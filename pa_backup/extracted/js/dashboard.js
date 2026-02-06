import { API } from './api.js';
import { AppState, StateManager } from './state.js';
import { CONSTANTS } from './constants.js';
import { UI, Modal } from './ui.js';


// We can attach startSession to window to make it accessible from HTML onclicks temporarily
// Or rewrite logic to use event listeners. For Refactor Phase 1, we stick to HTML onclick compat where possible or switch to listeners.
// Best approach: Dashboard logic builds HTML, it should attach listeners or use Global scope function.
// For now, I will export functions and index.html (or app.js) will expose them to window.

export const Dashboard = {
    async init() {
        await this.loadCourses();
        this.updateData();
    },

    async loadCourses() {
        try {
            const data = await API.course.list();
            const courses = data.courses || [];
            StateManager.update('allCourses', courses);

            const sel = document.getElementById('course-selector');
            if (sel) {
                sel.innerHTML = '';
                if (courses.length > 0) {
                    courses.forEach(c => {
                        const opt = document.createElement('option');
                        opt.value = c.id;
                        opt.text = c.name;
                        sel.appendChild(opt);
                    });

                    // Restore selection
                    if (AppState.courseId) {
                        sel.value = AppState.courseId;
                    } else {
                        // Default to first
                        StateManager.update('courseId', courses[0].id);
                        StateManager.saveLocal(CONSTANTS.LOCAL_KEYS.COURSE_ID, courses[0].id);
                    }
                }

                // Bind Change Event
                sel.onchange = () => this.handleCourseChange();
            }
        } catch (e) {
            console.error("Courses load error:", e);
        }
    },

    async handleCourseChange() {
        const sel = document.getElementById('course-selector');
        const newId = parseInt(sel.value);
        StateManager.update('courseId', newId);
        StateManager.saveLocal(CONSTANTS.LOCAL_KEYS.COURSE_ID, newId);
        await this.updateData();
    },

    async updateData() {
        try {
            const courseId = AppState.courseId;
            const userId = AppState.user.user_id;

            // 1. Update Header
            if (AppState.allCourses.length) {
                const currentCourse = AppState.allCourses.find(c => c.id == courseId);
                if (currentCourse) {
                    const nameEl = document.getElementById('dashboard-course-name');
                    const statsEl = document.getElementById('dashboard-course-stats');
                    if (nameEl) nameEl.textContent = currentCourse.name;
                    if (statsEl) statsEl.textContent = `${currentCourse.total_words} Kelime • General`;
                }
            }

            // 2. Fetch Units
            const data = await API.course.getUnitsStatus(courseId, userId);
            const units = (data.units || []).map(u => ({
                ...u,
                id: u.unit_id,
                is_locked: u.status !== "OPEN",
                progress: u.progress || { seen: 0, total: 0 }
            }));

            this.renderUnits(units);
            this.updateModeUI(); // Update mode switcher UI

        } catch (error) {
            console.error("Dashboard update error:", error);
            const container = document.getElementById('dashboard-units-container');
            if (container) {
                container.innerHTML = `
                    <div class="p-4 bg-red-50 text-red-600 rounded-xl border border-red-100 text-center">
                        <p class="font-bold">Veriler yüklenemedi.</p>
                        <button id="retry-dashboard" class="mt-2 text-sm underline">Tekrar Dene</button>
                    </div>
                `;
                document.getElementById('retry-dashboard').onclick = () => this.updateData();
            }
        }
    },

    renderUnits(units) {
        const container = document.getElementById('dashboard-units-container');
        if (!container) return;
        container.innerHTML = '';

        let totalSeen = 0;
        let totalCount = 0;
        let nextPlayableId = null;

        units.forEach((unit, index) => {
            totalSeen += unit.progress.seen || 0;
            totalCount += unit.progress.total || 0;

            if (!nextPlayableId && !unit.is_locked && (unit.progress.seen < unit.progress.total)) {
                nextPlayableId = unit.unit_id;
            }

            // Helper to determine status
            const unlockedStatuses = ['OPEN', 'active', 'completed', 'open'];
            const isLocked = unit.is_locked && !unlockedStatuses.includes(unit.status);
            const progressPercent = unit.progress.total > 0 ? Math.round((unit.progress.seen / unit.progress.total) * 100) : 0;

            // Render Card HTML
            const card = document.createElement('div');
            // ... (Use same logic as before for styles) ...
            // Simplified for brevity in this extraction, adhering to previous implementation

            let cardClass = 'bg-white border-2 rounded-2xl shadow-lg p-4 mb-3 transition-all duration-300';
            let iconBg = '';
            let iconContent = '';
            let statusHtml = '';

            if (isLocked) {
                cardClass += ' border-gray-100 bg-gray-50 opacity-60 cursor-not-allowed';
                iconBg = "bg-gray-200 text-gray-400";
                iconContent = '<i class="fas fa-lock text-lg"></i>';
                statusHtml = '<span class="px-2 py-0.5 bg-gray-100 text-gray-400 text-xs font-black rounded-full ml-2">KİLİTLİ</span>';
                card.onclick = () => Modal.show('Kilitli Ünite', 'Bu üniteyi açmak için önceki üniteyi tamamlamalısınız.', null, 'Tamam', 'bg-gray-500 hover:bg-gray-600');
            } else {
                cardClass += ' hover:shadow-xl hover:scale-[1.02] cursor-pointer group';
                // Click Action: We need to trigger startStudySession. 
                // We will emit a custom event or call globally exposed function.
                card.onclick = () => window.dispatchEvent(new CustomEvent('study-start', { detail: { unitId: unit.unit_id } }));

                iconBg = "bg-green-100 text-green-600";
                iconContent = `<span class="font-black text-lg">${index + 1}</span>`;
            }
            // ... (HTML construction) ...
            // For Safety, I'll use innerHTML injection for the complex card structure but bind onclick via element variable if possible, 
            // OR just use the onclick string referencing global function if we expose it (Phase 1 easiest path).
            // Let's go with Global Function Exposure strategy for Phase 1.

            // Re-using the HTML templating from index.html for visual consistency
            const prevUnit = units[index - 1];
            if (isLocked && prevUnit && prevUnit.progress.total > 0 && prevUnit.progress.seen === prevUnit.progress.total) {
                // Coming Soon state
                cardClass = cardClass.replace("opacity-60", "opacity-80");
                statusHtml = '<span class="px-2 py-0.5 bg-blue-100 text-blue-600 text-xs font-black rounded-full ml-2">YAKINDA</span>';
            }

            card.className = cardClass;
            card.innerHTML = `
                <div class="flex items-center justify-between pointer-events-none"> <!-- content wrapper -->
                    <div class="flex items-center gap-4">
                        <div class="w-14 h-14 rounded-2xl flex items-center justify-center ${iconBg}">
                            ${iconContent}
                        </div>
                        <div>
                            <div class="flex items-center">
                                <h4 class="font-black text-gray-800 text-lg">${unit.name || (index + 1) + '. Ünite'}</h4>
                                ${statusHtml}
                            </div>
                            <div class="flex items-center gap-2 mt-1">
                                <p class="text-sm font-semibold text-gray-500">${unit.progress.total} Kelime</p>
                                ${!isLocked ? `
                                    <div class="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden ml-2">
                                        <div class="h-full bg-green-500 rounded-full" style="width: ${progressPercent}%"></div>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                     ${!isLocked ? '<div class="w-8 h-8 rounded-full bg-green-50 flex items-center justify-center group-hover:bg-green-500 group-hover:text-white transition-colors text-green-500"><i class="fas fa-play text-sm ml-0.5"></i></div>' : ''}
                </div>
            `;

            container.appendChild(card);
        });

        // Overall Progress
        const overallPercent = totalCount > 0 ? Math.round((totalSeen / totalCount) * 100) : 0;
        const progressBar = document.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = `${overallPercent}%`;
            const pt = progressBar.parentElement.previousElementSibling.querySelector('.text-green-600');
            if (pt) pt.textContent = `%${overallPercent}`;
        }

        // Update "Start Button" logic
        if (!nextPlayableId && units.length > 0) nextPlayableId = units[0].unit_id;
        const mainBtn = document.querySelector('button[id="btn-main-start"]'); // We need to add ID to button in HTML
        if (mainBtn) {
            mainBtn.onclick = () => window.dispatchEvent(new CustomEvent('study-start', { detail: { unitId: nextPlayableId } }));
        }
    },

    updateModeUI() {
        const mode = AppState.studyMode;
        const wordsBtn = document.getElementById('btn-mode-words');
        const sentencesBtn = document.getElementById('btn-mode-sentences');
        const description = document.getElementById('mode-description');

        if (wordsBtn && sentencesBtn) {
            if (mode === 'words') {
                wordsBtn.className = 'flex-1 py-3 rounded-xl font-bold transition-all bg-green-500 text-white shadow-md';
                sentencesBtn.className = 'flex-1 py-3 rounded-xl font-bold transition-all bg-gray-100 text-gray-600 hover:bg-gray-200';
                if (description) description.textContent = 'Kelimeleri resim ve seslerle öğrenin.';
            } else {
                wordsBtn.className = 'flex-1 py-3 rounded-xl font-bold transition-all bg-gray-100 text-gray-600 hover:bg-gray-200';
                sentencesBtn.className = 'flex-1 py-3 rounded-xl font-bold transition-all bg-green-500 text-white shadow-md';
                if (description) description.textContent = 'Öğrendiğiniz kelimelerle cümle kurma pratiği yapın.';
            }
        }
    }
};
