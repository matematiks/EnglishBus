import { CONSTANTS } from './constants.js';

export const API = {
    baseUrl: CONSTANTS.API_URL,

    async request(endpoint, method = 'GET', body = null) {
        const options = {
            method,
            headers: { 'Content-Type': 'application/json' }
        };

        // Add Authorization header if token exists
        const token = localStorage.getItem(CONSTANTS.LOCAL_KEYS.TOKEN);
        if (token) {
            options.headers['Authorization'] = `Bearer ${token}`;
        }

        if (body) options.body = JSON.stringify(body);

        try {
            const res = await fetch(`${this.baseUrl}${endpoint}`, options);
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || `API Error: ${res.status}`);
            return data;
        } catch (err) {
            console.error("API Request Failed:", endpoint, err);
            throw err;
        }
    },

    auth: {
        async login(username, password) {
            return API.request('/auth/login', 'POST', { username, password });
        },
        async register(username, password) {
            return API.request('/auth/register', 'POST', { username, password });
        }
    },

    session: {
        async start(userId, courseId, unitId) {
            return API.request('/session/start', 'POST', {
                user_id: userId,
                course_id: courseId,
                unit_id: unitId
            });
        },
        async complete(userId, courseId, completedIds) {
            return API.request('/session/complete', 'POST', {
                user_id: userId,
                course_id: courseId,
                completed_word_ids: completedIds
            });
        },
        async reset(userId, courseId, password) {
            // Note: userId is ignored by backend (uses token), but kept for signature consistency if needed.
            // Backend expects ResetRequest: { course_id, password }
            return API.request('/reset', 'POST', { course_id: courseId, password });
        }
    },

    course: {
        async list() {
            return API.request('/courses');
        },
        async getUnitsStatus(courseId, userId) {
            return API.request(`/courses/${courseId}/units/status?user_id=${userId}`);
        }
    },

    practice: {
        async getSentences(userId, courseId, count) {
            return API.request(`/practice/sentences?user_id=${userId}&course_id=${courseId}&limit=${count}`);
        }
    }
};
