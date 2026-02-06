from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from backend.api.dependencies import get_db
from backend.api.models import UserRoleUpdateRequest

router = APIRouter()

@router.get("/users")
def get_all_users(db: sqlite3.Connection = Depends(get_db)):
    """Get all users for admin panel"""
    cursor = db.execute("""
        SELECT id, username, account_type, approval_status, teacher_id, 
               assigned_teacher_id, created_at, approved_at
        FROM Users
        ORDER BY created_at DESC
    """)
    
    users = []
    for row in cursor.fetchall():
        users.append({
            "id": row[0],
            "username": row[1],
            "account_type": row[2] or "individual",
            "approval_status": row[3] or "approved",
            "teacher_id": row[4],
            "assigned_teacher_id": row[5],
            "created_at": row[6],
            "approved_at": row[7]
        })
    
    return {"users": users}

@router.get("/stats")
def get_stats(db: sqlite3.Connection = Depends(get_db)):
    """Get statistics for admin dashboard"""
    
    # Total users
    total = db.execute("SELECT COUNT(*) FROM Users").fetchone()[0]
    
    # Teachers
    teachers = db.execute("SELECT COUNT(*) FROM Users WHERE account_type = 'teacher'").fetchone()[0]
    
    # Students (includes individual)
    students = db.execute("SELECT COUNT(*) FROM Users WHERE account_type != 'teacher' OR account_type IS NULL").fetchone()[0]
    
    # Pending teachers
    pending = db.execute("""
        SELECT COUNT(*) FROM Users 
        WHERE account_type = 'teacher' AND approval_status = 'pending_approval'
    """).fetchone()[0]
    
    return {
        "total_users": total,
        "teachers": teachers,
        "students": students,
        "pending_teachers": pending
    }

@router.get("/users/activity")
def get_user_activity(db: sqlite3.Connection = Depends(get_db)):
    """Get all users with activity status"""
    cursor = db.execute("""
        SELECT id, username, account_type, last_login, created_at, 
               teacher_id, approval_status
        FROM Users 
        WHERE approval_status = 'approved' OR approval_status IS NULL
        ORDER BY username
    """)
    
    import datetime
    users = []
    
    for row in cursor.fetchall():
        # Calculate activity status
        last_activity = row[3] or row[4]  # last_login or created_at
        if last_activity:
            try:
                if isinstance(last_activity, str):
                    last_dt = datetime.datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                else:
                    last_dt = last_activity
                days_ago = (datetime.datetime.now() - last_dt).days
            except:
                days_ago = 999
        else:
            days_ago = 999
        
        # Determine status
        if days_ago < 3:
            status = "active"
        elif days_ago < 7:
            status = "warning"
        else:
            status = "risk"
        
        users.append({
            "id": row[0],
            "username": row[1],
            "account_type": row[2] or "individual",
            "teacher_id": row[5],
            "approval_status": row[6] or "approved",
            "days_since_login": days_ago,
            "status": status
        })
    
    return {"users": users}

@router.get("/users/{user_id}")
def get_user_detail(user_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Get detailed information about a specific user"""
    cursor = db.execute("""
        SELECT id, username, account_type, created_at, last_login,
               teacher_id, assigned_teacher_id, approval_status
        FROM Users WHERE id = ?
    """, (user_id,))
    
    row = cursor.fetchone()
    if not row:
        return {"error": "User not found"}, 404
    
    # Calculate days since last activity
    import datetime
    last_activity = row[4] or row[3]  # last_login or created_at
    if last_activity:
        try:
            if isinstance(last_activity, str):
                last_dt = datetime.datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
            else:
                last_dt = last_activity
            days_ago = (datetime.datetime.now() - last_dt).days
        except:
            days_ago = 0
    else:
        days_ago = 0
    
    return {
        "id": row[0],
        "username": row[1],
        "account_type": row[2] or "individual",
        "created_at": row[3],
        "last_login": row[4],
        "teacher_id": row[5],
        "assigned_teacher_id": row[6],
        "approval_status": row[7] or "approved",
        "days_since_login": days_ago,
        "word_count": 0,  # Placeholder - can be calculated from progress table
        "progress_percent": 0  # Placeholder
    }

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Delete a user and all their progress"""
    # Check if user exists
    cursor = db.execute("SELECT username FROM Users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="User not found")
        
    try:
        # Cascade delete
        db.execute("DELETE FROM UserProgress WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM UserCourseProgress WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM Users WHERE id = ?", (user_id,))
        db.commit()
        return {"status": "success", "message": "User deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users/{user_id}/reset-password")
def reset_user_password(user_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Reset user password to default '123456'"""
    from backend.api.security_utils import get_password_hash
    
    # Check if user exists
    cursor = db.execute("SELECT username FROM Users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="User not found")
        
    try:
        default_pwd_hash = get_password_hash("123456")
        db.execute("UPDATE Users SET password_hash = ? WHERE id = ?", (default_pwd_hash, user_id))
        db.commit()
        return {"status": "success", "message": "Password reset to 123456"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int, 
    req: UserRoleUpdateRequest, 
    db: sqlite3.Connection = Depends(get_db)
):
    """Update user account type"""
    
    # Verify User Exists
    cursor = db.execute("SELECT username, account_type FROM Users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
        
    username, current_type = row
    
    # Don't allow changing own role if it's the only admin
    if user_id == req.admin_id:
        if req.account_type != "admin" and current_type == "admin":
             count = db.execute("SELECT COUNT(*) FROM Users WHERE account_type = 'admin'").fetchone()[0]
             if count <= 1:
                  raise HTTPException(status_code=400, detail="Cannot remove the last admin.")

    try:
        # If promoting to teacher, auto-approve
        approval_status = 'approved' if req.account_type == 'teacher' else 'approved'
        
        teacher_id = None
        if req.account_type == 'teacher':
             # Check if they already have one
             cursor = db.execute("SELECT teacher_id FROM Users WHERE id = ?", (user_id,))
             result = cursor.fetchone()
             if result and result[0]:
                  teacher_id = result[0]
             else:
                  # Generate new
                  import random
                  import string
                  for _ in range(100):
                      tid = ''.join(random.choices(string.digits, k=5))
                      # Check uniqueness
                      if not db.execute("SELECT 1 FROM Users WHERE teacher_id = ?", (tid,)).fetchone():
                          teacher_id = tid
                          break
        
        if req.account_type == 'teacher' and teacher_id:
             db.execute("UPDATE Users SET account_type=?, approval_status=?, teacher_id=? WHERE id=?", 
                        (req.account_type, approval_status, teacher_id, user_id))
        else:
             db.execute("UPDATE Users SET account_type=?, approval_status=? WHERE id=?", 
                        (req.account_type, approval_status, user_id))
        
        db.commit()
        return {
            "status": "success", 
            "message": f"User '{username}' role updated to '{req.account_type}'"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
