CREATE TABLE Courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        total_words INTEGER DEFAULT 0,
        owner_user_id INTEGER,
        order_number INTEGER DEFAULT 0
    , level TEXT DEFAULT 'General');
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
    , password_hash TEXT, is_admin INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT '2024-01-01 00:00:00', last_login TIMESTAMP, is_teacher INTEGER DEFAULT 0, teacher_id TEXT, assigned_teacher_id TEXT, account_type VARCHAR(20) DEFAULT 'individual', approval_status VARCHAR(20) DEFAULT 'approved', approved_by INTEGER DEFAULT NULL, approved_at TIMESTAMP DEFAULT NULL, settings_json TEXT DEFAULT '{}');
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
CREATE TABLE UserWordProgress (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, word_id INTEGER, repetition_count INTEGER DEFAULT 0, next_review_unix INTEGER DEFAULT 0, FOREIGN KEY(user_id) REFERENCES Users(id), FOREIGN KEY(word_id) REFERENCES Words(id));
CREATE INDEX idx_up_user_word ON UserProgress(user_id, word_id);
CREATE INDEX idx_words_course_unit ON Words(course_id, unit_id, order_number);
CREATE INDEX idx_units_course_order ON Units(course_id, order_number);
CREATE TABLE IF NOT EXISTS "TeacherStudents" (
	id INTEGER NOT NULL, 
	teacher_id INTEGER NOT NULL, 
	student_id INTEGER NOT NULL, 
	assigned_date DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(teacher_id) REFERENCES "Users" (id), 
	FOREIGN KEY(student_id) REFERENCES "Users" (id)
);
CREATE INDEX "ix_TeacherStudents_id" ON "TeacherStudents" (id);
CREATE TABLE IF NOT EXISTS "TeacherNotes" (
	id INTEGER NOT NULL, 
	teacher_id INTEGER NOT NULL, 
	student_id INTEGER NOT NULL, 
	note TEXT NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(teacher_id) REFERENCES "Users" (id), 
	FOREIGN KEY(student_id) REFERENCES "Users" (id)
);
CREATE INDEX "ix_TeacherNotes_id" ON "TeacherNotes" (id);
CREATE TABLE IF NOT EXISTS "StudentGoals" (
	id INTEGER NOT NULL, 
	student_id INTEGER NOT NULL, 
	teacher_id INTEGER NOT NULL, 
	goal_type VARCHAR NOT NULL, 
	target_value INTEGER NOT NULL, 
	current_value INTEGER, 
	deadline DATETIME, 
	completed INTEGER, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES "Users" (id), 
	FOREIGN KEY(teacher_id) REFERENCES "Users" (id)
);
CREATE INDEX "ix_StudentGoals_id" ON "StudentGoals" (id);
CREATE TABLE IF NOT EXISTS "TeacherMessages" (
	id INTEGER NOT NULL, 
	teacher_id INTEGER NOT NULL, 
	student_id INTEGER NOT NULL, 
	message_type VARCHAR NOT NULL, 
	subject VARCHAR, 
	message TEXT NOT NULL, 
	sent_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	read_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(teacher_id) REFERENCES "Users" (id), 
	FOREIGN KEY(student_id) REFERENCES "Users" (id)
);
CREATE INDEX "ix_TeacherMessages_id" ON "TeacherMessages" (id);
CREATE TABLE maintenance_mode (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    is_active BOOLEAN DEFAULT 0,
                    message TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by INTEGER
                );
CREATE TABLE admin_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_user_id INTEGER NOT NULL,
                    action VARCHAR(50) NOT NULL,
                    target_user_id INTEGER,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
