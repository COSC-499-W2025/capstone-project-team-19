from typing import Generator
from sqlite3 import Connection

from fastapi import Header, HTTPException, Depends

from src.db import connect, init_schema, get_user_by_id


def get_db() -> Generator[Connection, None, None]:
    conn = connect()
    init_schema(conn)  # ensure tables exist for API requests
    try:
        yield conn
    finally:
        conn.close()


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

