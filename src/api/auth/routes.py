from fastapi import APIRouter, HTTPException, Depends, status
import sqlite3

from .security import hash_password, verify_password, create_access_token
from ..dependencies import get_jwt_secret, get_db, get_current_user_id
from ..schemas.auth import RegisterIn, LoginIn, TokenOut, ChangePasswordIn
from ..schemas.common import ApiResponse
from ...db.users import (
    get_user_auth_by_username,
    get_user_auth_by_id,
    create_user_with_password,
    update_user_password,
    delete_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
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
        user_id=user["user_id"],
        username=user["username"],
        expires_minutes=60
    )
    return TokenOut(access_token=token)

@router.delete("/delete-account", response_model=ApiResponse[None])
def delete_account(
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    deleted = delete_user(conn, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return ApiResponse(success=True, data=None, error=None)

@router.post("/change-password", response_model=ApiResponse[None])
def change_password(
    payload: ChangePasswordIn,
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    user = get_user_auth_by_id(conn, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user["hashed_password"] or not verify_password(payload.current_password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    password_hash = hash_password(payload.new_password)
    updated = update_user_password(conn, user_id, password_hash)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return ApiResponse(success=True, data=None, error=None)
