import { API } from './api.js';
import { AppState, StateManager } from './state.js';
import { CONSTANTS } from './constants.js';
import { UI } from './ui.js';

export const Auth = {
    async login(username, password) {
        // Support pulling from UI if no args (onclick handler)
        if (!username) {
            const userEl = document.getElementById('login-username');
            const passEl = document.getElementById('login-password');
            username = userEl ? userEl.value.trim() : '';
            password = passEl ? passEl.value.trim() : '';
        }

        if (!username || !password) {
            this.showError('login', 'Lütfen kullanıcı adı ve şifre giriniz.');
            return;
        }

        try {
            console.log("🔐 Logging in...", username);
            const response = await API.auth.login(username, password);

            if (response.status === 'success') {
                // Save Token and User
                StateManager.saveLocal(CONSTANTS.LOCAL_KEYS.TOKEN, response.access_token);
                // Also save user info needed for app
                const user = { username: response.username, user_id: response.user_id };
                StateManager.update('user', user);
                // Save user to local storage for persistence on refresh (handled by state manager usually, or we do it here)
                // Assuming AppState init loads from local storage.
                // We'll store a minimal user object or just rely on token decoding? 
                // For now, simpler to store user object too.
                // Save user to local storage for persistence on refresh
                localStorage.setItem(CONSTANTS.LOCAL_KEYS.USER, JSON.stringify(user));

                console.log("✅ Login success!");

                // Clear inputs
                document.getElementById('login-username').value = '';
                document.getElementById('login-password').value = '';

                // Trigger global event
                window.dispatchEvent(new CustomEvent('auth-login-success'));
            } else {
                this.showError('login', 'Giriş başarısız.');
            }
        } catch (e) {
            console.error("Login Error:", e);
            this.showError('login', e.message || 'Bağlantı hatası.');
        }
    },

    async register() {
        const username = document.getElementById('register-username').value.trim();
        const password = document.getElementById('register-password').value.trim();

        if (!username || !password) {
            this.showError('register', 'Lütfen tüm alanları doldurunuz.');
            return;
        }

        try {
            console.log("📝 Registering...", username);
            const response = await API.auth.register(username, password);

            if (response.status === 'success') {
                alert('Kayıt başarılı! Lütfen giriş yapınız.');
                UI.showScreen('login-screen');
                // Auto-fill login
                document.getElementById('login-username').value = username;
                document.getElementById('register-username').value = '';
                document.getElementById('register-password').value = '';
            } else {
                this.showError('register', response.message || 'Kayıt başarısız.');
            }
        } catch (e) {
            console.error("Register Error:", e);
            this.showError('register', e.message || 'Kayıt işlemi sırasında bir hata oluştu.');
        }
    },

    logout() {
        localStorage.removeItem(CONSTANTS.LOCAL_KEYS.TOKEN);
        localStorage.removeItem(CONSTANTS.LOCAL_KEYS.USER);
        StateManager.update('user', null);

        // Reload or show login
        UI.showScreen('login-screen');
        console.log("🔒 Logged out.");
    },

    showError(context, message) {
        const el = document.getElementById(`${context}-error`);
        if (el) {
            el.textContent = message;
            el.classList.remove('hidden');
            // Increase timeout to 10 seconds
            setTimeout(() => el.classList.add('hidden'), 10000);
        } else {
            alert(message);
        }
    }
};
