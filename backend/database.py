from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# Database Connection
# Database Connection
# Adjust path to match execution context (cd backend && python main.py)
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "englishbus.db")
print(f"DEBUG: database.py resolved DB_PATH to: {DB_PATH}")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL, 
    connect_args={
        "check_same_thread": False,
        "timeout": 30
    }
)

# Enable foreign keys for all connections
from sqlalchemy import event
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")  # Better concurrency
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def check_and_migrate_db():
    import sqlite3
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Check Users table columns
            cursor.execute("PRAGMA table_info(Users)")
            columns = [info[1] for info in cursor.fetchall()]
            
            if "created_at" not in columns:
                print("Migrating: Adding created_at to Users")
                # SQLite ADD COLUMN requires constant default.
                cursor.execute("ALTER TABLE Users ADD COLUMN created_at TIMESTAMP DEFAULT '2024-01-01 00:00:00'")
                
            if "last_login" not in columns:
                print("Migrating: Adding last_login to Users")
                cursor.execute("ALTER TABLE Users ADD COLUMN last_login TIMESTAMP")
            
            if "is_teacher" not in columns:
                print("Migrating: Adding is_teacher to Users")
                cursor.execute("ALTER TABLE Users ADD COLUMN is_teacher INTEGER DEFAULT 0")
            
            if "teacher_id" not in columns:
                print("Migrating: Adding teacher_id to Users")
                cursor.execute("ALTER TABLE Users ADD COLUMN teacher_id TEXT UNIQUE")
            
            if "assigned_teacher_id" not in columns:
                print("Migrating: Adding assigned_teacher_id to Users")
                cursor.execute("ALTER TABLE Users ADD COLUMN assigned_teacher_id TEXT")
                
            if "approved_at" not in columns:
                print("Migrating: Adding approved_at to Users")
                cursor.execute("ALTER TABLE Users ADD COLUMN approved_at TIMESTAMP")
            
            if "account_type" not in columns:
                print("Migrating: Adding account_type to Users")
                cursor.execute("ALTER TABLE Users ADD COLUMN account_type VARCHAR(20)")
            
            if "approval_status" not in columns:
                print("Migrating: Adding approval_status to Users")
                cursor.execute("ALTER TABLE Users ADD COLUMN approval_status VARCHAR(20) DEFAULT 'approved'")
            
            # Create maintenance_mode table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS maintenance_mode (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    is_active BOOLEAN DEFAULT 0,
                    message TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by INTEGER
                )
            """)
            
            # Create admin_logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_user_id INTEGER NOT NULL,
                    action VARCHAR(50) NOT NULL,
                    target_user_id INTEGER,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create TeacherMessages table (for Admin/Teacher -> Student communication)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS TeacherMessages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    sender_id INTEGER,
                    subject TEXT,
                    message TEXT,
                    message_type VARCHAR(20) DEFAULT 'general',
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    read_at TIMESTAMP,
                    FOREIGN KEY(student_id) REFERENCES Users(id)
                )
            """)
            
            conn.commit()
            print("Migration successful")
            
            # Additional Migration for Courses
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(Courses)")
                course_cols = [info[1] for info in cursor.fetchall()]
                if "level" not in course_cols:
                    print("Migrating: Adding level to Courses")
                    cursor.execute("ALTER TABLE Courses ADD COLUMN level TEXT DEFAULT 'General'")
                    conn.commit()

    except Exception as e:
        print(f"Migration Warning: {e}")

# Run migration on import invocation (simple approach for local app)
if os.path.exists(DB_PATH):
    check_and_migrate_db()

# Models
class Course(Base):
    __tablename__ = "Courses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    level = Column(String, default="General")
    total_words = Column(Integer, default=0)
    owner_user_id = Column(Integer, nullable=True)
    order_number = Column(Integer, default=0)

    units = relationship("Unit", back_populates="course")
    words = relationship("Word", back_populates="course")

class Unit(Base):
    __tablename__ = "Units"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("Courses.id"))
    name = Column(String)
    order_number = Column(Integer)
    word_count = Column(Integer, default=0)

    course = relationship("Course", back_populates="units")
    words = relationship("Word", back_populates="unit")

class Word(Base):
    __tablename__ = "Words"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("Courses.id"))
    unit_id = Column(Integer, ForeignKey("Units.id"))
    english = Column(String)
    turkish = Column(String)
    
    # Metadata
    image_url = Column(String, nullable=True)
    audio_en_url = Column(String, nullable=True)
    audio_tr_url = Column(String, nullable=True)
    order_number = Column(Integer)

    course = relationship("Course", back_populates="words")
    unit = relationship("Unit", back_populates="words")

class User(Base):
    __tablename__ = "Users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password_hash = Column(String, nullable=True)
    active_course_id = Column(Integer, nullable=True)
    is_admin = Column(Integer, default=0) # 0=False, 1=True (using Integer for SQLite boolean compatibility)
    is_teacher = Column(Integer, default=0) # 0=False, 1=True
    teacher_id = Column(String, unique=True, nullable=True)  # 5-digit unique ID for teachers
    assigned_teacher_id = Column(String, nullable=True)  # Teacher ID assigned to student
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

class UserWordProgress(Base):
    """
    DEPRECATED (2025-01-21): This model points to a dead/ghost table.
    Use 'UserProgress' for active learning data.
    Reserved for future cleanup or migration if needed.
    """
    __tablename__ = "UserWordProgress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.id"))
    word_id = Column(Integer, ForeignKey("Words.id"))
    repetition_count = Column(Integer, default=0)
    next_review_unix = Column(Integer, default=0)
    
    # Optional relationships if needed
    # user = relationship("User")
    # word = relationship("Word")

