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

def get_user_by_id(conn: sqlite3.Connection, user_id: int):
    row = conn.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (user_id,)
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

def get_user_auth_by_username(conn: sqlite3.Connection, username: str):
    norm = _normalize_username(username)
    row = conn.execute(
        "SELECT user_id, username, hashed_password FROM users WHERE LOWER(username)=LOWER(?)",
        (norm,),
    ).fetchone()
    return row if row else None

def get_user_auth_by_id(conn: sqlite3.Connection, user_id: int):
    row = conn.execute(
        "SELECT user_id, username, hashed_password FROM users WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    return row if row else None

def create_user_with_password(conn: sqlite3.Connection, username: str, email: Optional[str], password_hash: str) -> int:
    cur = conn.execute(
        "INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",
        (username.strip(), email, password_hash),
    )
    conn.commit()
    return int(cur.lastrowid)

def update_user_password(conn: sqlite3.Connection, user_id: int, password_hash: str) -> bool:
    cur = conn.execute(
        "UPDATE users SET hashed_password = ? WHERE user_id = ?",
        (password_hash, user_id),
    )
    conn.commit()
    return cur.rowcount > 0


def delete_user(conn: sqlite3.Connection, user_id: int) -> bool:
    """Delete a user and all associated data.

    New databases get ON DELETE CASCADE on every FK, but existing DBs
    created before the migration still have the old schema (SQLite's
    CREATE TABLE IF NOT EXISTS won't alter existing tables).  Explicitly
    delete from tables whose FKs may lack CASCADE in older databases.
    """
    conn.execute("PRAGMA foreign_keys = ON")

    # Tables whose FKs may lack CASCADE in pre-migration databases
    project_keys = [
        r[0] for r in conn.execute(
            "SELECT project_key FROM projects WHERE user_id = ?", (user_id,)
        ).fetchall()
    ]
    if project_keys:
        placeholders = ",".join("?" * len(project_keys))
        conn.execute(
            f"DELETE FROM project_versions WHERE project_key IN ({placeholders})",
            project_keys,
        )
    conn.execute("DELETE FROM user_tokens WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM external_consent WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM text_contribution_revisions WHERE user_id = ?", (user_id,))

    cur = conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    return cur.rowcount > 0
