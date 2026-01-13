from typing import Generator
from src.db import connect
from fastapi import Header, HTTPException

def get_db() -> Generator:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()

def get_current_user_id(x_user_id: int | None = Header(default=None)) -> int:
    # Temporary dev auth: read user id from request header. Later this should be replaced with real auth (JWT/session) w/o changing endpoints
    if x_user_id is None: 
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    return x_user_id