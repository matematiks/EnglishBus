from fastapi import APIRouter, Depends, HTTPException, status
import sqlite3
import json
import os
import sys
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api.dependencies import get_db, get_current_user
from backend.api.models import UserSettings, SettingsUpdateRequest
from backend.api.security_utils import verify_password

router = APIRouter()

class ResetProgressRequest(BaseModel):
    course_id: int = None
    password: str

@router.get("/user/settings", response_model=UserSettings)
def get_user_settings(current_user: sqlite3.Row = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    """Get user settings for current user"""
    user_id = current_user['id']
    cursor = db.execute("SELECT settings_json, active_course_id, account_type FROM Users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    
    settings_json = row[0]
    active_course_id = row[1]
    
    settings_data = {}
    if settings_json:
        try:
            settings_data = json.loads(settings_json)
        except:
            pass
            
    points = UserSettings().dict().keys()
    valid_data = {k: v for k, v in settings_data.items() if k in points}
    
    valid_data['active_course_id'] = active_course_id
    
    return UserSettings(**valid_data)

@router.patch("/user/settings")
def update_user_settings(update: SettingsUpdateRequest, current_user: sqlite3.Row = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    """Update user settings - Expects FULL object"""
    user_id = current_user['id']
    
    # Serialize incoming settings
    new_data = update.settings.dict()
    active_course_id = new_data.get('active_course_id')
    
    settings_to_store = new_data.copy()
    if 'active_course_id' in settings_to_store:
        del settings_to_store['active_course_id']
    
    try:
        if active_course_id is not None:
            db.execute("UPDATE Users SET settings_json = ?, active_course_id = ? WHERE id = ?", 
                      (json.dumps(settings_to_store), active_course_id, user_id))
        else:
            db.execute("UPDATE Users SET settings_json = ? WHERE id = ?", 
                      (json.dumps(settings_to_store), user_id))
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    new_data['active_course_id'] = active_course_id 
    return {"status": "success", "settings": new_data}

@router.post("/user/reset-progress")
def reset_user_progress(request: ResetProgressRequest, current_user: sqlite3.Row = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    """Resets user progress SECURELY by verifying password first"""
    user_id = current_user['id']
    
    # Verify Password
    if not verify_password(request.password, current_user['password_hash']):
         raise HTTPException(status_code=403, detail="Şifre hatalı.")
    
    try:
        # Wipe UserProgress
        db.execute("DELETE FROM UserProgress WHERE user_id = ?", (user_id,))
        # Wipe UserCourseProgress
        db.execute("DELETE FROM UserCourseProgress WHERE user_id = ?", (user_id,))
        # Also clean session table if exists (SessionState)
        db.execute("DELETE FROM SessionState WHERE user_id = ?", (user_id,))
        
        db.commit()
        return {"status": "success", "message": "İlerleme başarıyla sıfırlandı."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
