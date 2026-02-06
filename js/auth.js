import { API } from './api.js';
import { AppState, StateManager } from './state.js';
import { CONSTANTS } from './constants.js';
import { UI } from './ui.js';
import { Loader } from './loader.js';
import { Dashboard } from './dashboard.js';

export const Auth = {
    async init() {
        // No form listeners needed as we use onclick handlers in HTML
        this.checkSession();
    },

    async checkSession() {
        const storedUser = localStorage.getItem(CONSTANTS.LOCAL_KEYS.USER);
        const token = localStorage.getItem(CONSTANTS.LOCAL_KEYS.TOKEN);

        if (storedUser && token) {
            try {
                const user = JSON.parse(storedUser);
                StateManager.update('user', user);

                // Show dashboard and init data
                UI.showScreen('dashboard-screen');
                await Dashboard.init();

                // Start Message Listener
                this.startMessageListener();
            } catch (e) {
                console.error("Session invalid", e);
                this.logout();
            }
        } else {
            UI.showScreen('login-screen');
        }
    },

    async login() {
        const usernameInput = document.getElementById('login-username');
        const passwordInput = document.getElementById('login-password');
        const errorDiv = document.getElementById('login-error');

        if (!usernameInput || !passwordInput) return;

        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();

        if (!username || !password) {
            this.showError(errorDiv, 'Lütfen kullanıcı adı ve şifre girin.');
            return;
        }

        Loader.show();
        errorDiv.classList.add('hidden');

        try {
            const res = await API.auth.login(username, password);
            if (res.status === 'success') {
                // Determine Account Type & ID
                // Backend returns: user_id, username, account_type, teacher_id
                const userData = {
                    id: res.user_id,
                    username: res.username,
                    accountType: res.account_type,
                    teacherId: res.teacher_id
                };

                // Persist Session
                localStorage.setItem(CONSTANTS.LOCAL_KEYS.USER, JSON.stringify(userData));
                localStorage.setItem(CONSTANTS.LOCAL_KEYS.TOKEN, res.access_token);

                // Update State
                StateManager.update('user', userData);

                // Initialize Dashboard
                await Dashboard.init();
                UI.showScreen('dashboard-screen');

                // Trigger global event for App.js
                window.dispatchEvent(new CustomEvent('auth-login-success'));

                this.startMessageListener();
            } else {
                this.showError(errorDiv, res.message || 'Giriş yapılamadı.');
            }
        } catch (err) {
            this.showError(errorDiv, 'Sunucu hatası: ' + err.message);
        } finally {
            Loader.hide();
        }
    },

    async register() {
        const usernameInput = document.getElementById('register-username');
        const passwordInput = document.getElementById('register-password');
        const isTeacherCheck = document.getElementById('register-is-teacher');
        const teacherIdInput = document.getElementById('register-teacher-id');
        const errorDiv = document.getElementById('register-error');

        const username = usernameInput?.value.trim();
        const password = passwordInput?.value.trim();
        const accountType = isTeacherCheck?.checked ? 'teacher' : 'student';
        const teacherId = accountType === 'student' ? teacherIdInput?.value.trim() : null;

        if (!username || !password) {
            this.showError(errorDiv, 'Tüm alanları doldurun.');
            return;
        }

        Loader.show();
        if (errorDiv) errorDiv.classList.add('hidden');

        try {
            const res = await API.auth.register(username, password, accountType, teacherId);

            if (res.status === 'success') {
                alert(res.message || 'Kayıt başarılı! Giriş yapabilirsiniz.');
                // Auto switch to login
                UI.showScreen('login-screen');
                // Optional: Prefill login
                document.getElementById('login-username').value = username;
            } else {
                this.showError(errorDiv, res.detail || 'Kayıt başarısız.');
            }
        } catch (err) {
            this.showError(errorDiv, 'Hata: ' + err.message);
        } finally {
            Loader.hide();
        }
    },

    logout() {
        localStorage.clear(); // Clear all app data
        window.location.reload();
    },

    showError(element, message) {
        if (element) {
            element.textContent = message;
            element.classList.remove('hidden');
        } else {
            alert(message);
        }
    },

    // --- Message Listener ---
    startMessageListener() {
        if (this.messageInterval) clearInterval(this.messageInterval);
        this.checkMessages();
        this.messageInterval = setInterval(() => this.checkMessages(), 60000);
    },

    async checkMessages() {
        const user = AppState.user;
        if (!user || user.accountType !== 'student') return;

        try {
            const res = await API.request(`/messages/student/${user.id}`);
            if (res && res.messages) {
                const unreadCount = res.messages.filter(m => !m.read_at).length;
                this.updateBadge(unreadCount);
            }
        } catch (e) {
            // fail silently
        }
    },

    updateBadge(count) {
        const badge = document.getElementById('dashboard-msg-badge');
        if (badge) {
            if (count > 0) {
                badge.textContent = count;
                badge.classList.remove('hidden');
                badge.classList.add('flex');
            } else {
                badge.classList.add('hidden');
                badge.classList.remove('flex');
            }
        }
    }
};
