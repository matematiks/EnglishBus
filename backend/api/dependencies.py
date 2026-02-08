"""
Database dependency for FastAPI
Provides SQLite connection via dependency injection
"""

import sqlite3
import os
from typing import Generator

# Database path relative to backend directory
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "../englishbus.db")


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Dependency that provides database connection.
    
    Usage in endpoints:
    Dependency that provides a database connection.
    Ensures connection is properly closed after request.
    
    CRITICAL: check_same_thread=False required for FastAPI async
    """
    # Normalize path
    db_path = os.path.normpath(DATABASE_PATH)
    
    # Connect
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    
    try:
        yield conn
    finally:
        conn.close()

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from api.security_utils import decode_access_token
import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: sqlite3.Connection = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    # Security Fix: SELECT specific columns instead of *
    # Prevents password hash leak and unnecessary data transfer    
    cursor = db.execute("""
        SELECT id, username, active_course_id, is_teacher, account_type
        FROM Users 
        WHERE id = ?
    """, (int(user_id),))
    user = cursor.fetchone()
    if user is None:
        raise credentials_exception
    return user

