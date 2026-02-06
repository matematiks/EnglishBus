from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class TeacherStudent(Base):
    __tablename__ = "TeacherStudents"
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
    assigned_date = Column(DateTime(timezone=True), server_default=func.now())

class TeacherNote(Base):
    __tablename__ = "TeacherNotes"
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
    note = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class StudentGoal(Base):
    __tablename__ = "StudentGoals"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
    goal_type = Column(String, nullable=False)  # 'daily', 'weekly', 'monthly', 'custom'
    target_value = Column(Integer, nullable=False)
    current_value = Column(Integer, default=0)
    deadline = Column(DateTime, nullable=True)
    completed = Column(Integer, default=0)  # 0=False, 1=True
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TeacherMessage(Base):
    __tablename__ = "TeacherMessages"
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
    message_type = Column(String, nullable=False)  # 'general', 'motivation', 'warning', 'congratulation'
    subject = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime, nullable=True)
