"""
src/db/resumes.py

Helpers for storing and retrieving frozen resume snapshots.
"""
from __future__ import annotations

import sqlite3
from typing import Dict, List, Any, Optional

def insert_resume_snapshot(
    conn: sqlite3.Connection,
    user_id: int,
    name: str,
    resume_json: str,
    rendered_text: Optional[str] = None,
) -> int:
    """
    Insert a new resume snapshot. Returns the inserted row id.
    """
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO resume_snapshots (user_id, name, resume_json, rendered_text)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, name, resume_json, rendered_text),
    )
    conn.commit()
    return cur.lastrowid


def list_resumes(conn: sqlite3.Connection, user_id: int) -> List[Dict[str, Any]]:
    """
    List stored resume snapshots for a user, newest first.
    """
    rows = conn.execute(
        """
        SELECT id, name, created_at
        FROM resume_snapshots
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (user_id,),
    ).fetchall()
    return [{"id": r[0], "name": r[1], "created_at": r[2]} for r in rows]


def get_resume_snapshot(conn: sqlite3.Connection, user_id: int, resume_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch a specific resume snapshot by id for a user.
    """
    row = conn.execute(
        """
        SELECT id, name, resume_json, rendered_text, created_at
        FROM resume_snapshots
        WHERE user_id = ? AND id = ?
        """,
        (user_id, resume_id),
    ).fetchone()

    if not row:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "resume_json": row[2],
        "rendered_text": row[3],
        "created_at": row[4],
    }

def update_resume_snapshot(
    conn: sqlite3.Connection,
    user_id: int,
    resume_id: int,
    resume_json: str,
    rendered_text: Optional[str] = None,
) -> None:
    """
    Update an existing resume snapshot's JSON + rendered text.
    """
    conn.execute(
        """
        UPDATE resume_snapshots
        SET resume_json = ?, rendered_text = ?
        WHERE user_id = ? AND id = ?
        """,
        (resume_json, rendered_text, user_id, resume_id),
    )
    conn.commit()


def delete_resume_snapshot(
    conn: sqlite3.Connection,
    user_id: int,
    resume_id: int,
) -> bool:
    """
    Permanently delete a resume snapshot for a user.
    Returns True if a row was deleted, False otherwise.
    """
    cur = conn.execute(
        """
        DELETE FROM resume_snapshots
        WHERE user_id = ? AND id = ?
        """,
        (user_id, resume_id),
    )
    conn.commit()
    return cur.rowcount > 0


def delete_all_user_resumes(conn: sqlite3.Connection, user_id: int) -> int:
    """
    Delete all resume snapshots for a user. Returns count of deleted resumes.
    """
    cur = conn.execute(
        """
        DELETE FROM resume_snapshots
        WHERE user_id = ?
        """,
        (user_id,),
    )
    conn.commit()
    return cur.rowcount