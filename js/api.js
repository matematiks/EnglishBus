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
        async register(username, password, accountType = 'individual', teacherId = null) {
            return API.request('/auth/register', 'POST', {
                username,
                password,
                account_type: accountType,
                teacher_id: teacherId
            });
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
            // Backend expects ResetProgressRequest: { course_id, password }
            return API.request('/user/reset-progress', 'POST', { course_id: courseId, password });
        }
    },

    study: {
        async getSession(userId, courseId, unitId) {
            let url = `/api/study/session?user_id=${userId}&course_id=${courseId}`;
            if (unitId) url += `&unit_id=${unitId}`;
            return API.request(url);
        },
        async record(userId, courseId, wordId, quality) {
            // quality: 0-5
            return API.request('/api/study/record', 'POST', {
                user_id: userId,
                course_id: courseId,
                word_id: wordId,
                quality: quality
            });
        }
    },

    course: {
        async list() {
            return API.request('/courses');
        },
        async getUnitsStatus(courseId, userId) {
            return API.request(`/courses/${courseId}/units/status?user_id=${userId}`);
        },
        async getRepetitionStats(courseId, userId) {
            return API.request(`/courses/${courseId}/stats/repetition?user_id=${userId}`);
        }
    },

    practice: {
        async getSentences(userId, courseId, count) {
            return API.request(`/practice/sentences?user_id=${userId}&course_id=${courseId}&limit=${count}`);
        }
    }
};
