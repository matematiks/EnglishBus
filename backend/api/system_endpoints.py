from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import sqlite3
from backend.api.dependencies import get_db

router = APIRouter()

class MaintenanceModeRequest(BaseModel):
    is_active: bool
    message: Optional[str] = ""

class LogFilterRequest(BaseModel):
    limit: Optional[int] = 50

# Helper function for logging
def log_admin_action(db: sqlite3.Connection, admin_id: int, action: str, target_user_id: Optional[int] = None, details: str = ""):
    """Log admin actions to database"""
    db.execute("""
        INSERT INTO admin_logs (admin_user_id, action, target_user_id, details)
        VALUES (?, ?, ?, ?)
    """, (admin_id, action, target_user_id, details))
    db.commit()

@router.get("/maintenance-mode")
def get_maintenance_mode(db: sqlite3.Connection = Depends(get_db)):
    """Get current maintenance mode status"""
    cursor = db.execute("SELECT is_active, message FROM maintenance_mode ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    
    return {
        "is_active": bool(row[0]) if row else False,
        "message": row[1] if row else ""
    }

@router.post("/maintenance-mode")
def set_maintenance_mode(request: MaintenanceModeRequest, db: sqlite3.Connection = Depends(get_db)):
    """Set maintenance mode on/off"""
    ADMIN_USER_ID = 1
    
    db.execute("""
        INSERT INTO maintenance_mode (is_active, message, updated_by)
        VALUES (?, ?, ?)
    """, (request.is_active, request.message, ADMIN_USER_ID))
    db.commit()
    
    # Log the action
    log_admin_action(db, ADMIN_USER_ID, "maintenance_mode_change", None, 
                     f"Active: {request.is_active}, Message: {request.message[:50]}")
    
    return {"status": "success", "is_active": request.is_active}

@router.get("/logs")
def get_admin_logs(limit: int = 50, db: sqlite3.Connection = Depends(get_db)):
    """Get admin action logs"""
    cursor = db.execute("""
        SELECT al.id, al.admin_user_id, u1.username as admin_name, 
               al.action, al.target_user_id, u2.username as target_name,
               al.details, al.created_at
        FROM admin_logs al
        LEFT JOIN Users u1 ON al.admin_user_id = u1.id
        LEFT JOIN Users u2 ON al.target_user_id = u2.id
        ORDER BY al.created_at DESC
        LIMIT ?
    """, (limit,))
    
    logs = []
    for row in cursor.fetchall():
        logs.append({
            "id": row[0],
            "admin_user_id": row[1],
            "admin_name": row[2] or "Unknown",
            "action": row[3],
            "target_user_id": row[4],
            "target_name": row[5],
            "details": row[6],
            "created_at": row[7]
        })
    
    return {"logs": logs}

# Export this function for use in other modules
__all__ = ['log_admin_action', 'router']
