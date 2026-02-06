import { AppState, StateManager } from './state.js';
import { UI, Modal } from './ui.js';
import { Auth } from './auth.js';
import { Dashboard } from './dashboard.js';
import { StudyEngine } from './study.js';
import { CONSTANTS } from './constants.js';
import { API } from './api.js';

// ========== INITIALIZATION ==========
async function initApp() {
    console.log("🚀 App Init Started");

    // Auth Check
    if (AppState.user) {
        document.getElementById('dashboard-username').textContent = AppState.user.username;
        document.getElementById('user-initial').textContent = AppState.user.username[0].toUpperCase();

        UI.showScreen('dashboard-screen');
        await Dashboard.init();
    } else {
        UI.showScreen('login-screen');
    }
}

// ========== EVENT BINDING ==========
document.addEventListener('DOMContentLoaded', () => {
    // 1. App Init
    initApp();

    // 2. Auth Listeners
    const loginBtn = document.getElementById('btn-login-action');
    if (loginBtn) loginBtn.addEventListener('click', () => Auth.login());

    const regBtn = document.getElementById('btn-register-action');
    if (regBtn) regBtn.addEventListener('click', () => Auth.register());

    // 3. Global UI Listeners
    // Custom Events
    window.addEventListener('auth-login-success', () => initApp());
    window.addEventListener('study-start', (e) => StudyEngine.start(e.detail.unitId));

    // 4. Study Screen Actions
    const cardEl = document.querySelector('.perspective-1000'); // Assuming card container class or ID
    // Actually the card click is on the card div itself in the HTML structure which is dynamically generated in prev version?
    // StartStudySession builds DOM? No, index.html has static Study structure.

    const flipArea = document.getElementById('study-card-container'); // Need to verify ID
    // In index.html, the card container is `cursor-pointer relative w-full h-96 ...` with onclick="handleCardAction()"
    // We need to attach listener if we remove onclick.
    // For Phase 1 Compatibility, we expose functions to window.
});


// ========== LEGACY / HTML EXPOSURE ==========
// To keep index.html onclicks working without changing every line of HTML yet.
window.showScreen = UI.showScreen;
window.handleLogin = () => Auth.login();
window.handleRegister = () => Auth.register();
window.startStudySession = (unitId) => StudyEngine.start(unitId);
window.handleCardAction = () => StudyEngine.handleAction();
window.handleLogout = () => {
    Modal.show(
        'Çıkış Yap',
        'Hesabınızdan çıkış yapmak istediğinize emin misiniz?',
        () => Auth.logout(),
        'Çıkış Yap',
        'bg-red-500 hover:bg-red-600'
    );
};
window.setStudyMode = (mode) => {
    StateManager.update('studyMode', mode);
    StateManager.saveLocal(CONSTANTS.LOCAL_KEYS.MODE, mode);
};

window.switchStudyMode = (mode) => {
    StateManager.update('studyMode', mode);
    StateManager.saveLocal(CONSTANTS.LOCAL_KEYS.MODE, mode);

    // Update UI
    if (typeof Dashboard !== 'undefined' && Dashboard.updateModeUI) {
        Dashboard.updateModeUI();
    }

    // Show feedback
    const modeText = mode === 'words' ? '📖 Kelime Kartları' : '📝 Cümle Pratiği';
    console.log(`✅ Mod değiştirildi: ${modeText}`);
};
window.confirmReset = () => {
    Modal.show(
        'İlerlemeyi Sıfırla',
        'Tüm ilerlemeniz silinecek. Emin misiniz?',
        async () => {
            try {
                await API.session.reset(AppState.user.user_id, AppState.courseId);
                alert('İlerleme sıfırlandı!');
                await Dashboard.updateData();
            } catch (e) {
                alert('Sıfırlama başarısız: ' + e.message);
            }
        },
        'Sıfırla',
        'bg-red-600 hover:bg-red-700'
    );
};
window.exitStudy = () => {
    UI.showScreen('dashboard-screen');
    Dashboard.updateData();
};

// Expose Modal for HTML (already imported at top)
window.Modal = Modal;

window.updateDashboardData = () => Dashboard.updateData();

// Debug globals
window.AppState = AppState;
