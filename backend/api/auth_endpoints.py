from fastapi import APIRouter, Depends, HTTPException, status
import sqlite3
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.dependencies import get_db
from api.models import UserRegisterRequest, UserLoginRequest
from api.security_utils import get_password_hash, verify_password, create_access_token

router = APIRouter()

@router.post("/register")
def register(user: UserRegisterRequest, db: sqlite3.Connection = Depends(get_db)):
    # Check if user exists
    cursor = db.execute("SELECT id FROM Users WHERE username = ?", (user.username,))
    if cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu kullanıcı adı zaten alınmış."
        )

    # Validate teacher_id if student account
    if user.account_type == 'student' and user.teacher_id:
        cursor = db.execute("""
            SELECT id FROM Users 
            WHERE teacher_id = ? 
            AND account_type = 'teacher' 
            AND approval_status = 'approved'
        """, (user.teacher_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Geçersiz veya onaylanmamış öğretmen ID'si."
            )

    # Hash Password
    pwd_hash = get_password_hash(user.password)

    # Determine approval status
    approval_status = 'pending_approval' if user.account_type == 'teacher' else 'approved'
    
    # Insert User
    try:
        db.execute("""
            INSERT INTO Users (username, password_hash, account_type, approval_status, assigned_teacher_id) 
            VALUES (?, ?, ?, ?, ?)
        """, (user.username, pwd_hash, user.account_type, approval_status, 
              user.teacher_id if user.account_type == 'student' else None))
        db.commit()
        
        if user.account_type == 'teacher':
            return {
                "status": "success", 
                "message": "Öğretmen hesabınız oluşturuldu. Admin onayı bekleniyor.",
                "requires_approval": True
            }
        else:
            return {
                "status": "success", 
                "message": "Kayıt başarılı! Giriş yapabilirsiniz.",
                "requires_approval": False
            }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
def login(user: UserLoginRequest, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.execute("""
        SELECT id, username, password_hash, account_type, approval_status, teacher_id 
        FROM Users WHERE username = ?
    """, (user.username,))
    row = cursor.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı."
        )

    user_id, username, stored_hash, account_type, approval_status, teacher_id = row
    
    if not stored_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bu hesabın şifresi ayarlanmamış. Lütfen yönetici ile iletişime geçin."
        )

    # Check approval status
    if approval_status == 'pending_approval':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hesabınız henüz onaylanmadı. Admin onayı bekleniyor."
        )
    
    if approval_status == 'rejected':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hesabınız yönetici tarafından reddedildi."
        )

    if not verify_password(user.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı."
        )

    # Update last login
    db.execute("UPDATE Users SET last_login = datetime('now') WHERE id = ?", (user_id,))
    db.commit()

    # Create JWT token
    token = create_access_token({"sub": str(user_id), "username": username})
    return {
        "status": "success", 
        "user_id": user_id, 
        "username": username, 
        "account_type": account_type,
        "teacher_id": teacher_id,
        "access_token": token, 
        "token_type": "bearer"
    }
