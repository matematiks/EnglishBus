export const CONSTANTS = {
    API_URL: (() => {
        // If file:// or dev server (port 3000-3999), use localhost:8000
        if (window.location.protocol === 'file:' ||
            (window.location.port >= 3000 && window.location.port <= 3999)) {
            return 'http://localhost:8000';
        }
        // Production: same origin
        return '';
    })(),
    LOCAL_KEYS: {
        USER: 'englishbus_user',
        DAILY_GOAL: 'englishbus_daily_goal',
        MODE: 'englishbus_mode',
        PROFILE: 'englishbus_profile',
        LANGUAGE: 'englishbus_language',
        TOKEN: 'englishbus_token',
    },
    DEFAULTS: {
        DAILY_GOAL: 5,
        STUDY_MODE: 'words',
        LANGUAGE: 'en',
        USER_ID: 1
    }
};
