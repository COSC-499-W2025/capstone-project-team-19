"""
src/db/user_experience.py

Helpers for storing and retrieving experience entries used by resume export.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional


def _clean_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def list_user_experience_entries(conn: sqlite3.Connection, user_id: int) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            entry_id,
            role,
            company,
            date_text,
            description,
            display_order,
            created_at,
            updated_at
        FROM user_experience_entries
        WHERE user_id = ?
        ORDER BY display_order ASC, entry_id ASC
        """,
        (user_id,),
    ).fetchall()

    return [
        {
            "entry_id": row[0],
            "role": row[1],
            "company": row[2],
            "date_text": row[3],
            "description": row[4],
            "display_order": row[5],
            "created_at": row[6],
            "updated_at": row[7],
        }
        for row in rows
    ]


def add_user_experience_entry(
    conn: sqlite3.Connection,
    user_id: int,
    *,
    role: str,
    company: Optional[str] = None,
    date_text: Optional[str] = None,
    description: Optional[str] = None,
) -> int:
    clean_role = _clean_optional_text(role)
    clean_company = _clean_optional_text(company)
    clean_date_text = _clean_optional_text(date_text)
    clean_description = _clean_optional_text(description)

    if not clean_role:
        raise ValueError("role is required")

    row = conn.execute(
        """
        SELECT COALESCE(MAX(display_order), 0)
        FROM user_experience_entries
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()
    next_order = int(row[0] or 0) + 1

    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO user_experience_entries
        (user_id, role, company, date_text, description, display_order, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (
            user_id,
            clean_role,
            clean_company,
            clean_date_text,
            clean_description,
            next_order,
        ),
    )
    conn.commit()
    return cur.lastrowid


def delete_user_experience_entry(conn: sqlite3.Connection, user_id: int, entry_id: int) -> bool:
    cur = conn.execute(
        """
        DELETE FROM user_experience_entries
        WHERE user_id = ? AND entry_id = ?
        """,
        (user_id, entry_id),
    )
    conn.commit()
    return cur.rowcount > 0