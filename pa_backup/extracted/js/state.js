import { CONSTANTS } from './constants.js';

export const AppState = {
    user: JSON.parse(localStorage.getItem(CONSTANTS.LOCAL_KEYS.USER)) || null,
    courseId: parseInt(localStorage.getItem(CONSTANTS.LOCAL_KEYS.COURSE_ID)) || CONSTANTS.DEFAULTS.COURSE_ID,
    unitId: null, // Active unit in session
    currentStep: 1,
    cardData: [],
    currentCardIndex: 0,
    isFlipped: false,
    dailyGoal: parseInt(localStorage.getItem(CONSTANTS.LOCAL_KEYS.DAILY_GOAL)) || CONSTANTS.DEFAULTS.DAILY_GOAL,
    completedBatchIds: [],
    studyMode: localStorage.getItem(CONSTANTS.LOCAL_KEYS.MODE) || CONSTANTS.DEFAULTS.STUDY_MODE,
    // User profile (display name & avatar)
    profile: JSON.parse(localStorage.getItem(CONSTANTS.LOCAL_KEYS.PROFILE)) || { displayName: '', avatarUrl: '' },
    // UI language (en/tr)
    language: localStorage.getItem(CONSTANTS.LOCAL_KEYS.LANGUAGE) || CONSTANTS.DEFAULTS.LANGUAGE,

    // UI Specific State
    allCourses: [],
    lastCelebratedCount: 0,
    unitProgress: null // { new_words: 0, total: 50 }
};

// Simple Observer Pattern
const listeners = [];

export const StateManager = {
    subscribe(fn) {
        listeners.push(fn);
    },
    notify() {
        listeners.forEach(fn => fn(AppState));
    },
    update(key, value) {
        AppState[key] = value;
        this.notify();
    },
    saveLocal(key, value) {
        localStorage.setItem(key, value);
    }
};
