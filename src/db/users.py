"""
src/db/users.py

Handles all database operations related to users:
 - Creating new users
 - Fetching existing users
 - Normalizing usernames for lookups
"""

import sqlite3
from typing import Optional, Tuple


def _normalize_username(username: str) -> str:
    """Trim whitespace and prepare username for case-insensitive lookups."""
    return username.strip()


def get_user_by_username(conn: sqlite3.Connection, username: str) -> Optional[Tuple[int, str, Optional[str]]]:
    """Case-insensitive lookup."""
    norm = _normalize_username(username)
    row = conn.execute(
        "SELECT user_id, username, email FROM users WHERE LOWER(username)=LOWER(?)",
        (norm,),
    ).fetchone()
    return row if row else None


def get_or_create_user(conn: sqlite3.Connection, username: str, email: Optional[str] = None) -> int:
    """Return existing user_id or create new user."""
    existing = get_user_by_username(conn, username)
    if existing:
        return existing[0]
    cur = conn.execute(
        "INSERT INTO users (username, email) VALUES (?, ?)",
        (username.strip(), email),
    )
    conn.commit()
    return cur.lastrowid