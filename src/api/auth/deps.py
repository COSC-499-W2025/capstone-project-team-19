from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
import sqlite3
import jwt

from .security import decode_access_token
from src.db.users import get_user_by_id
from src.api.dependencies import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET is not set")
    return secret

def get_current_user(
    token: str = Depends(oauth2_scheme),
    conn: sqlite3.Connection = Depends(get_db),
):
    try:
        payload = decode_access_token(secret=get_jwt_secret(), token=token)
        user_id = int(payload["sub"])
    except (KeyError, ValueError, jwt.PyJWTError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user = get_user_by_id(conn, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {"id": user["user_id"], "username": user["username"]}
