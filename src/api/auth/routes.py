from fastapi import APIRouter, HTTPException, Depends, status
import sqlite3

from .security import hash_password, verify_password, create_access_token
from .deps import get_jwt_secret, get_db
from ..schemas.auth import RegisterIn, LoginIn, TokenOut
from ...db.users import get_user_auth_by_username, create_user_with_password

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
def register(payload: RegisterIn, conn: sqlite3.Connection = Depends(get_db)):
    existing = get_user_auth_by_username(conn, payload.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
    
    password_hash = hash_password(payload.password)
    user_id = create_user_with_password(conn, payload.username, None, password_hash)
    
    return {"user_id": user_id, "username": payload.username}

@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, conn: sqlite3.Connection = Depends(get_db)):
    user = get_user_auth_by_username(conn, payload.username)
    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    token = create_access_token(
        secret=get_jwt_secret(),
        user_id=user["user id"],
        username=user["username"],
        expires_minutes=60
    )
    return TokenOut(access_token=token)