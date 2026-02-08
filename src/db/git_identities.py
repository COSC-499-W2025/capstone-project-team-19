from __future__ import annotations

from typing import Dict, List
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
