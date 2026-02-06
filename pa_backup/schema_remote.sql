CREATE TABLE Courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        total_words INTEGER DEFAULT 0,
        owner_user_id INTEGER,
        order_number INTEGER DEFAULT 0
    );
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE Units (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        name TEXT,
        order_number INTEGER,
        word_count INTEGER DEFAULT 0,
        FOREIGN KEY(course_id) REFERENCES Courses(id)
    );
CREATE TABLE Words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        unit_id INTEGER,
        english TEXT,
        turkish TEXT,
        image_url TEXT,
        audio_en_url TEXT,
        audio_tr_url TEXT,
        order_number INTEGER,
        FOREIGN KEY(course_id) REFERENCES Courses(id),
        FOREIGN KEY(unit_id) REFERENCES Units(id)
    );
CREATE TABLE Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        active_course_id INTEGER
    , password_hash TEXT, is_admin INTEGER DEFAULT 0);
CREATE TABLE UserProgress (
        user_id INTEGER,
        word_id INTEGER,
        repetition_count INTEGER DEFAULT 0,
        next_review_step INTEGER DEFAULT 0, last_updated TEXT DEFAULT NULL, first_learned_at TEXT DEFAULT NULL,
        PRIMARY KEY (user_id, word_id)
    );
CREATE TABLE UserCourseProgress (
        user_id INTEGER,
        course_id INTEGER,
        current_step INTEGER DEFAULT 1,
        last_activity TIMESTAMP, max_open_unit_order INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY (user_id, course_id)
    );
CREATE INDEX idx_up_user_word ON UserProgress(user_id, word_id);
CREATE INDEX idx_words_course_unit ON Words(course_id, unit_id, order_number);
CREATE INDEX idx_units_course_order ON Units(course_id, order_number);
CREATE TABLE UserWordProgress (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, word_id INTEGER, repetition_count INTEGER DEFAULT 0, next_review_unix INTEGER DEFAULT 0, FOREIGN KEY(user_id) REFERENCES Users(id), FOREIGN KEY(word_id) REFERENCES Words(id));
