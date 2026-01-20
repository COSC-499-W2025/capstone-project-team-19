from typing import Generator
from sqlite3 import Connection
import os
import jwt

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.db import connect, init_schema
from src.db.users import get_user_by_id
from src.api.auth.security import decode_access_token


def get_db() -> Generator[Connection, None, None]:
    conn = connect()
    init_schema(conn)  # ensure tables exist for API requests
    try:
        yield conn
    finally:
        conn.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET is not set")
    return secret

def get_current_user(
    token: str = Depends(oauth2_scheme),
    conn: Connection = Depends(get_db),
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

def get_current_user_id(
    current_user: dict = Depends(get_current_user),
) -> int:
    """Extract user_id from the current authenticated user."""
    return current_user["id"]

def get_current_user_id(
    conn: Connection = Depends(get_db),
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
) -> int:
    # Temporary dev auth: read user id from request header. Later replace with real auth (JWT/session)
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")

    user = get_user_by_id(conn, x_user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return x_user_id

