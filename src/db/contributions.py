"""
src/db/contributions.py

Handles collaborative text and code contribution tracking:
 - Storing revision-level details
 - Summarizing user contributions
"""

import sqlite3
from typing import Dict, Any


def store_text_contribution_revision(conn: sqlite3.Connection, revision: Dict[str, Any]) -> None:
    """
    Store a text contribution revision record.
    """
    timestamp = revision.get("revision_timestamp")
    if hasattr(timestamp, "isoformat"):
        timestamp = timestamp.isoformat()
    conn.execute("""
        INSERT INTO text_contribution_revisions (
            user_id, drive_file_id, revision_id, words_added, revision_text, revision_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        revision["user_id"],
        revision["drive_file_id"],
        revision["revision_id"],
        revision.get("words_added", 0),
        revision.get("revision_text"),
        timestamp,
    ))
    conn.commit()


def store_text_contribution_summary(conn: sqlite3.Connection, summary: Dict[str, Any]) -> None:
    """
    Store or update a text contribution summary record.
    """
    conn.execute("""
        INSERT INTO text_contribution_summary (
            user_id, project_name, drive_file_id, user_revision_count, total_word_count, total_revision_count
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, project_name, drive_file_id) DO UPDATE SET
            user_revision_count=excluded.user_revision_count,
            total_word_count=excluded.total_word_count,
            total_revision_count=excluded.total_revision_count
    """, (
        summary["user_id"],
        summary["project_name"],
        summary["drive_file_id"],
        summary.get("user_revision_count", 0),
        summary.get("total_word_count", 0),
        summary.get("total_revision_count", 0),
    ))
    conn.commit()