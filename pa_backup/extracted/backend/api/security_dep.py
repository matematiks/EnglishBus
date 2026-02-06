from fastapi import Header, HTTPException, status
from typing import Optional
from .security_utils import decode_access_token

async def get_current_user(authorization: Optional[str] = Header(None)) -> int:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")
    token = authorization.split(" ")[1]
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
        return user_id
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
