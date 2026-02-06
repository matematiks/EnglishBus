"""
Admin endpoints for teacher approval system
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import sqlite3
import random
import string
from datetime import datetime
from api.dependencies import get_db

router = APIRouter()

class ApproveTeacherRequest(BaseModel):
    teacher_user_id: int
    admin_user_id: int

class RejectTeacherRequest(BaseModel):
    teacher_user_id: int
    admin_user_id: int
    reason: str = ""

def generate_teacher_id(db: sqlite3.Connection) -> str:
    """Generate unique 5-digit teacher ID"""
    max_attempts = 100
    for _ in range(max_attempts):
        teacher_id = ''.join(random.choices(string.digits, k=5))
        # Check if unique
        cursor = db.execute("SELECT id FROM Users WHERE teacher_id = ?", (teacher_id,))
        if not cursor.fetchone():
            return teacher_id
    raise Exception("Could not generate unique teacher ID")

@router.get("/pending-teachers")
def get_pending_teachers(db: sqlite3.Connection = Depends(get_db)):
    """Get list of teachers awaiting approval"""
    cursor = db.execute("""
        SELECT id, username, created_at 
        FROM Users 
        WHERE account_type = 'teacher' 
        AND approval_status = 'pending_approval'
        ORDER BY created_at ASC
    """)
    
    teachers = []
    for row in cursor.fetchall():
        teachers.append({
            "id": row[0],
            "username": row[1],
            "created_at": row[2]
        })
    
    return {"pending_teachers": teachers}

@router.post("/approve-teacher")
def approve_teacher(req: ApproveTeacherRequest, db: sqlite3.Connection = Depends(get_db)):
    """Approve a teacher and assign them a 5-digit ID"""
    
    # Check if teacher exists and is pending
    cursor = db.execute("""
        SELECT id, username, approval_status 
        FROM Users 
        WHERE id = ? AND account_type = 'teacher'
    """, (req.teacher_user_id,))
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(404, "Teacher not found")
    
    if row[2] == 'approved':
        raise HTTPException(400, "Teacher already approved")
    
    # Generate unique teacher ID
    teacher_id = generate_teacher_id(db)
    
    # Update teacher record - IMPORTANT: Also set account_type to ensure it's 'teacher'
    db.execute("""
        UPDATE Users 
        SET account_type = 'teacher',
            approval_status = 'approved',
            teacher_id = ?,
            approved_by = ?,
            approved_at = datetime('now')
        WHERE id = ?
    """, (teacher_id, req.admin_user_id, req.teacher_user_id))
    
    db.commit()
    
    # TODO: Send email/notification to teacher with their ID
    
    return {
        "success": True,
        "teacher_id": teacher_id,
        "message": f"Teacher '{row[1]}' approved with ID: {teacher_id}"
    }

@router.post("/reject-teacher")
def reject_teacher(req: RejectTeacherRequest, db: sqlite3.Connection = Depends(get_db)):
    """Reject a teacher application"""
    
    # Check if teacher exists
    cursor = db.execute("""
        SELECT id, username 
        FROM Users 
        WHERE id = ? AND account_type = 'teacher'
    """, (req.teacher_user_id,))
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(404, "Teacher not found")
    
    # Update teacher record
    db.execute("""
        UPDATE Users 
        SET approval_status = 'rejected',
            approved_by = ?,
            approved_at = datetime('now')
        WHERE id = ?
    """, (req.admin_user_id, req.teacher_user_id))
    
    db.commit()
    
    # TODO: Send notification to user
    
    return {
        "success": True,
        "message": f"Teacher '{row[1]}' rejected"
    }
