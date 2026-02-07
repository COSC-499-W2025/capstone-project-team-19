from __future__ import annotations

import os
from typing import Dict, List, Optional
import sqlite3

from src.utils.helpers import ensure_table


def ensure_user_github_table(conn: sqlite3.Connection) -> None:
    ensure_table(
        conn,
        "user_github",
        """
        CREATE TABLE IF NOT EXISTS user_github (
            user_id     INTEGER NOT NULL,
            email       TEXT,
            name        TEXT,
            created_at  TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, email, name)
        )
        """,
    )


def load_user_github(conn: sqlite3.Connection, user_id: int) -> Dict[str, set]:
    emails, names = set(), set()
    cur = conn.execute("SELECT email, name FROM user_github WHERE user_id = ?", (user_id,))
    for em, nm in cur.fetchall():
        if em:
            emails.add(em.strip().lower())
        if nm:
            names.add(nm.strip().lower())
    return {"emails": emails, "names": names}


def save_user_github(conn: sqlite3.Connection, user_id: int, emails: List[str], names: List[str]) -> None:
    cur = conn.cursor()
    for em in set(e.strip().lower() for e in emails if e.strip()):
        cur.execute(
            "INSERT OR IGNORE INTO user_github(user_id, email, name) VALUES (?, ?, NULL)",
            (user_id, em),
        )
    for nm in set(n.strip() for n in names if n.strip()):
        cur.execute(
            "INSERT OR IGNORE INTO user_github(user_id, email, name) VALUES (?, NULL, ?)",
            (user_id, nm),
        )
    conn.commit()


def get_project_classification_by_id(
    conn: sqlite3.Connection,
    user_id: int,
    project_id: int,
    zip_name_raw: str,
) -> Optional[Dict[str, str]]:
    zip_name_stem = os.path.splitext(zip_name_raw)[0]
    row = conn.execute(
        """
        SELECT project_name, classification, project_type
        FROM project_classifications
        WHERE classification_id = ?
          AND user_id = ?
          AND zip_name IN (?, ?)
        """,
        (project_id, user_id, zip_name_raw, zip_name_stem),
    ).fetchone()
    if not row:
        return None
    return {
        "project_name": row[0],
        "classification": row[1],
        "project_type": row[2],
    }
