from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import sqlite3
from backend.api.dependencies import get_db

router = APIRouter(prefix="/admin/messages", tags=["admin-messages"])

class SendMessageRequest(BaseModel):
    recipient_type: str  # 'user', 'all_teachers', 'all_students', 'all_users'
    recipient_id: Optional[int] = None
    subject: str
    message: str
    message_type: str = 'general'
    admin_user_id: int

def send_message_to_user(db: sqlite3.Connection, user_id: int, sender_id: int, subject: str, message: str, message_type: str = 'general'):
    """Helper function to insert a message to a specific user"""
    try:
        db.execute("""
            INSERT INTO TeacherMessages (student_id, sender_id, subject, message, message_type, sent_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (user_id, sender_id, subject, message, message_type))
        db.commit()
    except Exception as e:
        print(f"Error sending message to user {user_id}: {e}")
        # Don't raise here to allow bulk sending to continue for other users
        # But we should log it.

@router.post("/send")
def send_admin_message(request: SendMessageRequest, db: sqlite3.Connection = Depends(get_db)):
    """
    Send message from admin to user(s)
    """
    try:
        messages_sent = 0
        
        if request.recipient_type == 'user':
            # Send to single user
            if not request.recipient_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="recipient_id gerekli"
                )
            send_message_to_user(db, request.recipient_id, request.admin_user_id, request.subject, request.message, request.message_type)
            messages_sent = 1
            
        elif request.recipient_type == 'all_teachers':
            # Get all approved teachers
            cursor = db.execute("""
                SELECT id FROM Users 
                WHERE account_type = 'teacher' 
                AND approval_status = 'approved'
            """)
            teachers = cursor.fetchall()
            for (teacher_id,) in teachers:
                send_message_to_user(db, teacher_id, request.admin_user_id, request.subject, request.message, request.message_type)
                messages_sent += 1
                
        elif request.recipient_type == 'all_students':
            # Get all students
            cursor = db.execute("""
                SELECT id FROM Users 
                WHERE account_type = 'student'
            """)
            students = cursor.fetchall()
            for (student_id,) in students:
                send_message_to_user(db, student_id, request.admin_user_id, request.subject, request.message, request.message_type)
                messages_sent += 1
                
        elif request.recipient_type == 'all_users':
            # Get all approved users
            cursor = db.execute("""
                SELECT id FROM Users 
                WHERE approval_status = 'approved'
            """)
            users = cursor.fetchall()
            for (user_id,) in users:
                send_message_to_user(db, user_id, request.admin_user_id, request.subject, request.message, request.message_type)
                messages_sent += 1
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Geçersiz recipient_type"
            )
        
        return {
            "status": "success",
            "message": f"{messages_sent} mesaj gönderildi",
            "count": messages_sent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/users/list")
def list_users_for_messaging(db: sqlite3.Connection = Depends(get_db)):
    """
    Get list of all users for message recipient selection
    """
    try:
        cursor = db.execute("""
            SELECT id, username, account_type, approval_status 
            FROM Users 
            WHERE approval_status = 'approved'
            ORDER BY account_type, username
        """)
        users = cursor.fetchall()
        
        return {
            "users": [
                {
                    "id": row[0],
                    "username": row[1],
                    "account_type": row[2] or "individual",
                    "approval_status": row[3]
                }
                for row in users
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
