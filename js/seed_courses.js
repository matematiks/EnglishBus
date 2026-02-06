
// Mock Data Loader for Offline Ecosystem
const DEMO_WORDS = [
    { id: 1, en: "hello", tr: "merhaba", img: "001.webp", aud: "ing_001.mp3" },
    { id: 2, en: "hi", tr: "selam", img: "hi.png", aud: "ing_002.mp3" },
    { id: 3, en: "I", tr: "ben", img: "I.png", aud: "ing_003.mp3" },
    { id: 4, en: "am", tr: "olmak", img: "004.webp", aud: "ing_004.mp3" },
    { id: 5, en: "you", tr: "sen", img: "you.png", aud: "ing_005.mp3" },
    { id: 6, en: "want", tr: "istemek", img: "want.png", aud: "ing_006.mp3" },
    { id: 7, en: "water", tr: "su", img: "water.png", aud: "ing_007.mp3" },
    { id: 8, en: "food", tr: "yiyecek", img: "food.png", aud: "ing_008.mp3" },
    { id: 9, en: "yes", tr: "evet", img: "yes.png", aud: "ing_009.mp3" },
    { id: 10, en: "no", tr: "hayır", img: "no.png", aud: "ing_010.mp3" },
    { id: 11, en: "please", tr: "lütfen", img: "please.png", aud: "ing_011.mp3" },
    { id: 12, en: "not", tr: "değil", img: "not.png", aud: "ing_012.mp3" },
    { id: 13, en: "me", tr: "bana", img: "me.png", aud: "ing_013.mp3" },
    { id: 14, en: "this", tr: "bu", img: "this.png", aud: "ing_014.mp3" },
    { id: 15, en: "what", tr: "ne", img: "015.webp", aud: "ing_015.mp3" },
    { id: 16, en: "give", tr: "vermek", img: "give.png", aud: "ing_016.mp3" },
    { id: 17, en: "take", tr: "almak", img: "take.png", aud: "ing_017.mp3" },
    { id: 18, en: "thanks", tr: "teşekkürler", img: "018.webp", aud: "ing_018.mp3" },
    { id: 19, en: "don't", tr: "yapma", img: "019.webp", aud: "ing_019.mp3" }
];

export const CourseSeeder = {
    seed() {
        // Construct Course Object
        const courses = [{
            id: 1,
            name: "DEPS 1 (Foundation)",
            level: "A1",
            total_words: DEMO_WORDS.length,
            units: [
                {
                    unit_id: 101,
                    name: "Tanışma & Temel Kavramlar",
                    words: DEMO_WORDS,
                    status: "OPEN",
                    progress: { seen: 0, total: DEMO_WORDS.length }
                },
                {
                    unit_id: 102,
                    name: "Günlük Yaşam (Demo)",
                    words: [],
                    status: "LOCKED",
                    progress: { seen: 0, total: 20 }
                }
            ]
        }];

        // Inject if empty or forced
        const existing = localStorage.getItem('englishbus_courses');
        if (!existing) {
            console.log("🌱 Seeding DEPS 1 Course Data...");
            localStorage.setItem('englishbus_courses', JSON.stringify(courses));
        }
    }
};

// Initialize
CourseSeeder.seed();
