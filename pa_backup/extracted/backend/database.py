from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# Database Connection
# Database Connection
# Adjust path to match execution context (cd backend && python main.py)
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "englishbus.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Models
class Course(Base):
    __tablename__ = "Courses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
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

class UserWordProgress(Base):
    __tablename__ = "UserWordProgress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.id"))
    word_id = Column(Integer, ForeignKey("Words.id"))
    repetition_count = Column(Integer, default=0)
    next_review_unix = Column(Integer, default=0)
    
    # Optional relationships if needed
    # user = relationship("User")
    # word = relationship("Word")

