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

    # Hash Password
    pwd_hash = get_password_hash(user.password)

    # Insert User
    try:
        db.execute(
            "INSERT INTO Users (username, password_hash) VALUES (?, ?)",
            (user.username, pwd_hash)
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "success", "message": "Kayıt başarılı! Giriş yapabilirsiniz."}

@router.post("/login")
def login(user: UserLoginRequest, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.execute("SELECT id, username, password_hash FROM Users WHERE username = ?", (user.username,))
    row = cursor.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı."
        )

    user_id, username, stored_hash = row
    if not stored_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bu hesabın şifresi ayarlanmamış. Lütfen yönetici ile iletişime geçin."
        )

    if not verify_password(user.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı."
        )

    # Create JWT token
    token = create_access_token({"sub": str(user_id), "username": username})
    return {"status": "success", "user_id": user_id, "username": username, "access_token": token, "token_type": "bearer"}
