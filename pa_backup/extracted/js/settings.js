// settings.js – handles Settings screen interactions
import { AppState, StateManager } from './state.js';
import { CONSTANTS } from './constants.js';
import { API } from './api.js'; // optional backend sync

// ========== LOAD SETTINGS ==========
function loadSettings() {
    // Load Daily Goal
    const goalSlider = document.getElementById('onpage-goal-slider');
    if (goalSlider) {
        // Default to 5 if null/undefined
        const currentGoal = AppState.dailyGoal !== undefined ? AppState.dailyGoal : 5;
        goalSlider.value = currentGoal;
        updateOnPageGoal(currentGoal);
    }
}
// saveSettings removed as it's no longer used (auto-save on slider change)




// ========== VIEW STATISTICS ==========
function viewStatistics() {
    // Gather statistics
    const stats = {
        totalWords: AppState.totalWords || 0,
        learnedWords: AppState.learnedWords || 0,
        streak: AppState.streak || 0,
        studyMode: AppState.studyMode || 'words',
        courseId: AppState.courseId || 1,
        dailyGoal: localStorage.getItem(CONSTANTS.LOCAL_KEYS.GOAL) || '5'
    };

    const percentage = stats.totalWords > 0
        ? Math.round((stats.learnedWords / stats.totalWords) * 100)
        : 0;

    // Create modal content
    const modalHtml = `
        <div id="stats-modal" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
            <div class="bg-white rounded-3xl w-11/12 max-w-md p-6 shadow-2xl">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-xl font-black text-gray-800">📊 İstatistikler</h3>
                    <button onclick="document.getElementById('stats-modal').remove()" class="text-gray-400 hover:text-gray-600">
                        <i class="fas fa-times text-xl"></i>
                    </button>
                </div>
                <div class="space-y-4">
                    <div class="bg-blue-50 rounded-xl p-4">
                        <div class="flex justify-between items-center">
                            <span class="text-gray-600">Öğrenilen Kelime</span>
                            <span class="text-2xl font-black text-blue-600">${stats.learnedWords} / ${stats.totalWords}</span>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-2 mt-2">
                            <div class="bg-blue-500 h-2 rounded-full" style="width: ${percentage}%"></div>
                        </div>
                        <p class="text-xs text-gray-400 mt-1 text-right">${percentage}% tamamlandı</p>
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div class="bg-green-50 rounded-xl p-3 text-center">
                            <p class="text-2xl font-black text-green-600">🔥 ${stats.streak}</p>
                            <p class="text-xs text-gray-500">Günlük Seri</p>
                        </div>
                        <div class="bg-purple-50 rounded-xl p-3 text-center">
                            <p class="text-2xl font-black text-purple-600">🎯 ${stats.dailyGoal}</p>
                            <p class="text-xs text-gray-500">Günlük Hedef</p>
                        </div>
                    </div>
                    <div class="bg-gray-50 rounded-xl p-3">
                        <div class="flex justify-between text-sm">
                            <span class="text-gray-500">Çalışma Modu</span>
                            <span class="font-bold text-gray-700">${stats.studyMode === 'words' ? '📖 Kelime Kartları' : '📝 Cümle Pratiği'}</span>
                        </div>
                    </div>
                </div>
                <button onclick="document.getElementById('stats-modal').remove()" 
                    class="w-full mt-4 py-3 bg-gray-900 text-white font-bold rounded-xl hover:bg-gray-800 transition-all">
                    Kapat
                </button>
            </div>
        </div>
    `;

    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

// ========== DANGER ZONE TOGGLE ==========
function toggleDangerZone() {
    const content = document.getElementById('danger-zone-content');
    const icon = document.getElementById('danger-zone-icon');

    if (content.classList.contains('hidden')) {
        content.classList.remove('hidden');
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
        // Populate courses when opening
        populateResetCourses();
    } else {
        content.classList.add('hidden');
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
    }
}

// ========== POPULATE COURSES FOR RESET ==========
function populateResetCourses() {
    const select = document.getElementById('reset-course-select');
    const btn = document.getElementById('reset-course-btn');
    if (!select) return;

    // Clear existing options except first
    select.innerHTML = '<option value="">-- Kurs Seçin --</option>';

    // Get courses from AppState or fetch from API
    const courses = AppState.allCourses || [];

    if (courses.length === 0) {
        // Try to fetch from course select dropdown
        const courseSelect = document.getElementById('course-selector');
        if (courseSelect) {
            Array.from(courseSelect.options).forEach(opt => {
                if (opt.value) {
                    const option = document.createElement('option');
                    option.value = opt.value;
                    option.textContent = opt.textContent;
                    select.appendChild(option);
                }
            });
        }
    } else {
        courses.forEach(course => {
            const option = document.createElement('option');
            option.value = course.id || course.course_id;
            option.textContent = course.name || course.title;
            select.appendChild(option);
        });
    }

    // Enable/disable button based on selection
    select.addEventListener('change', () => {
        btn.disabled = !select.value;
    });
}

// ========== RESET CONFIRMATION WITH PASSWORD ==========
function showResetConfirmation() {
    const select = document.getElementById('reset-course-select');
    if (!select || !select.value) {
        alert('⚠️ Lütfen sıfırlanacak kursu seçin!');
        return;
    }

    const courseId = select.value;
    const courseName = select.options[select.selectedIndex].textContent;

    // Store selected course for later use
    window._resetCourseId = courseId;
    window._resetCourseName = courseName;

    // First confirmation step
    const modalHtml = `
        <div id="reset-modal-step1" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
            <div class="bg-white rounded-3xl w-11/12 max-w-md p-6 shadow-2xl">
                <div class="text-center mb-4">
                    <div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-3">
                        <i class="fas fa-exclamation-triangle text-red-500 text-3xl"></i>
                    </div>
                    <h3 class="text-xl font-black text-gray-800">Emin misiniz?</h3>
                </div>
                <div class="bg-red-50 rounded-xl p-3 mb-4">
                    <p class="text-sm text-red-700 font-bold text-center">
                        <i class="fas fa-book mr-2"></i>${courseName}
                    </p>
                </div>
                <p class="text-gray-600 text-center text-sm mb-6">
                    Bu kursun tüm ilerleme verileri <strong class="text-red-600">kalıcı olarak silinecek</strong>. 
                    Bu işlem geri alınamaz!
                </p>
                <div class="space-y-3">
                    <button onclick="showPasswordConfirmation()"
                        class="w-full py-3 bg-red-500 text-white font-black rounded-xl hover:bg-red-600 transition-all">
                        Evet, Devam Et
                    </button>
                    <button onclick="document.getElementById('reset-modal-step1').remove()"
                        class="w-full py-3 bg-gray-100 text-gray-700 font-bold rounded-xl hover:bg-gray-200 transition-all">
                        İptal
                    </button>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

function showPasswordConfirmation() {
    // Remove first modal
    const step1 = document.getElementById('reset-modal-step1');
    if (step1) step1.remove();

    const courseName = window._resetCourseName || 'Seçili Kurs';

    // Second confirmation step with password
    const modalHtml = `
        <div id="reset-modal-step2" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
            <div class="bg-white rounded-3xl w-11/12 max-w-md p-6 shadow-2xl">
                <div class="text-center mb-4">
                    <div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-3">
                        <i class="fas fa-lock text-red-500 text-3xl"></i>
                    </div>
                    <h3 class="text-xl font-black text-gray-800">Şifre Doğrulama</h3>
                </div>
                <div class="bg-red-50 rounded-xl p-3 mb-4">
                    <p class="text-sm text-red-700 font-bold text-center">
                        <i class="fas fa-book mr-2"></i>${courseName}
                    </p>
                </div>
                <p class="text-gray-600 text-center mb-4 text-sm">
                    İşlemi onaylamak için hesap şifrenizi girin.
                </p>
                <div class="mb-4">
                    <input type="password" id="reset-password-input" 
                           class="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-red-500 focus:outline-none"
                           placeholder="Şifrenizi girin">
                    <p id="reset-password-error" class="hidden text-red-500 text-xs mt-2">
                        <i class="fas fa-times-circle"></i> Yanlış şifre
                    </p>
                </div>
                <div class="space-y-3">
                    <button onclick="executeReset()"
                        class="w-full py-3 bg-red-500 text-white font-black rounded-xl hover:bg-red-600 transition-all flex items-center justify-center gap-2">
                        <i class="fas fa-trash-alt"></i>
                        Sıfırla
                    </button>
                    <button onclick="document.getElementById('reset-modal-step2').remove()"
                        class="w-full py-3 bg-gray-100 text-gray-700 font-bold rounded-xl hover:bg-gray-200 transition-all">
                        İptal
                    </button>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Focus password input
    setTimeout(() => {
        const input = document.getElementById('reset-password-input');
        if (input) input.focus();
    }, 100);
}

async function executeReset() {
    const passwordInput = document.getElementById('reset-password-input');
    const errorMsg = document.getElementById('reset-password-error');
    const password = passwordInput ? passwordInput.value : '';
    const courseId = window._resetCourseId;
    const courseName = window._resetCourseName;

    if (!password) {
        if (passwordInput) passwordInput.classList.add('border-red-500');
        return;
    }

    try {
        // Execute reset via API for specific course
        if (API && API.session && API.session.reset) {
            // Note: userId is largely ignored by backend auth, but we pass valid ID if available
            await API.session.reset(AppState.user.user_id, courseId, password);

            // Remove modal on success
            const modal = document.getElementById('reset-modal-step2');
            if (modal) modal.remove();

            alert(`✅ "${courseName}" kursu başarıyla sıfırlandı!`);
            window.location.reload();
        } else {
            throw new Error("API bağlantısı sağlanamadı");
        }

        // Clean up
        delete window._resetCourseId;
        delete window._resetCourseName;

    } catch (error) {
        console.error('Reset error:', error);
        // Show error in modal
        if (errorMsg) {
            errorMsg.textContent = error.message || "Hatalı şifre veya sunucu hatası.";
            errorMsg.classList.remove('hidden');
        }
        if (passwordInput) {
            passwordInput.classList.add('border-red-500');
            passwordInput.value = '';
            passwordInput.focus();
        }
    }
}

// ========== DAILY GOAL SLIDER ==========
function updateOnPageGoal(value) {
    const display = document.getElementById('onpage-goal-display');
    if (!display) return;

    if (value == 0) {
        display.textContent = 'Hedef Yok';
        display.className = 'text-sm font-black text-gray-500 bg-gray-100 px-2 py-1 rounded-lg';
    } else {
        display.textContent = `${value} Kelime Hedefi`;
        display.className = 'text-sm font-black text-blue-600 bg-blue-50 px-2 py-1 rounded-lg';
    }
}

function saveOnPageGoal(value) {
    StateManager.update('dailyGoal', parseInt(value));
    localStorage.setItem(CONSTANTS.LOCAL_KEYS.GOAL, value);
    // Optional: Call UI update if needed elsewhere
    if (typeof UI !== 'undefined' && UI.updateGoalDisplay) {
        UI.updateGoalDisplay(value);
    }
}

// ========== EXPOSE TO GLOBAL SCOPE ==========
// ========== EXPOSE TO GLOBAL SCOPE ==========
window.loadSettings = loadSettings;
// window.saveSettings removed
// window.updateAvatarPreview removed
window.viewStatistics = viewStatistics;
window.toggleDangerZone = toggleDangerZone;
window.populateResetCourses = populateResetCourses;
window.showResetConfirmation = showResetConfirmation;
window.showPasswordConfirmation = showPasswordConfirmation;
window.executeReset = executeReset;
window.updateOnPageGoal = updateOnPageGoal;
window.saveOnPageGoal = saveOnPageGoal;

export { loadSettings, viewStatistics, toggleDangerZone, showResetConfirmation, updateOnPageGoal, saveOnPageGoal };
