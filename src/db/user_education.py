"""
src/db/user_education.py

Helpers for storing and retrieving education / certificate entries
used by resume export.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional


def _clean_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def list_user_education_entries(conn: sqlite3.Connection, user_id: int) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            entry_id,
            entry_type,
            title,
            organization,
            date_text,
            description,
            display_order,
            created_at,
            updated_at
        FROM user_education_entries
        WHERE user_id = ?
        ORDER BY display_order ASC, entry_id ASC
        """,
        (user_id,),
    ).fetchall()

    return [
        {
            "entry_id": row[0],
            "entry_type": row[1],
            "title": row[2],
            "organization": row[3],
            "date_text": row[4],
            "description": row[5],
            "display_order": row[6],
            "created_at": row[7],
            "updated_at": row[8],
        }
        for row in rows
    ]


def add_user_education_entry(
    conn: sqlite3.Connection,
    user_id: int,
    *,
    entry_type: str,
    title: str,
    organization: Optional[str] = None,
    date_text: Optional[str] = None,
    description: Optional[str] = None,
) -> int:
    clean_type = _clean_optional_text(entry_type)
    clean_title = _clean_optional_text(title)
    clean_organization = _clean_optional_text(organization)
    clean_date_text = _clean_optional_text(date_text)
    clean_description = _clean_optional_text(description)

    if clean_type not in {"education", "certificate"}:
        raise ValueError("entry_type must be 'education' or 'certificate'")
    if not clean_title:
        raise ValueError("title is required")

    row = conn.execute(
        """
        SELECT COALESCE(MAX(display_order), 0)
        FROM user_education_entries
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()
    next_order = int(row[0] or 0) + 1

    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO user_education_entries
        (user_id, entry_type, title, organization, date_text, description, display_order, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (
            user_id,
            clean_type,
            clean_title,
            clean_organization,
            clean_date_text,
            clean_description,
            next_order,
        ),
    )
    conn.commit()
    return cur.lastrowid


def delete_user_education_entry(conn: sqlite3.Connection, user_id: int, entry_id: int) -> bool:
    cur = conn.execute(
        """
        DELETE FROM user_education_entries
        WHERE user_id = ? AND entry_id = ?
        """,
        (user_id, entry_id),
    )
    conn.commit()
    return cur.rowcount > 0