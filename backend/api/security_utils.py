import os
import datetime
from typing import Optional
import jwt
import bcrypt
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Secret key for JWT (use env var in production)
# IMPORTANT: Strong default fallback to ensure production safety
SECRET_KEY = os.getenv("JWT_SECRET_KEY") or "qjFneqpLbX5bd1sT9WNi5v-vPzguDyjoL3gocD3dWxmiPtxw8BEnyKTeX6gFuEz1"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# Security: Validate JWT secret key length
# Minimum 32 bytes (256 bits) recommended for HMAC
if len(SECRET_KEY) < 32:
    logger.warning(
        f"JWT secret key is only {len(SECRET_KEY)} characters long. "
        "Minimum recommended length is 32 characters for security. "
        "Please set a strong JWT_SECRET_KEY environment variable."
    )
    # In production, you might want to raise an error instead:
    # raise ValueError("JWT secret must be at least 32 characters")
else:
    logger.info(f"JWT secret key length: {len(SECRET_KEY)} bytes ✓")

def get_password_hash(password: str) -> str:
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # Check if password matches
        # hashed_password must be bytes for bcrypt
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError as e:
        raise e
