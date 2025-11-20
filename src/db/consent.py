"""
src/db/consent.py

Handles database operations related to user consent and external consent:
 - Recording and retrieving consent statuses
 - Managing consent timestamps and user associations
"""

import sqlite3
from typing import Optional


def get_latest_consent(conn: sqlite3.Connection, user_id: int) -> Optional[str]:
    """Return most recent consent status for a user."""
    row = conn.execute(
        "SELECT status FROM consent_log WHERE user_id=? ORDER BY timestamp DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    return row[0] if row else None


def get_latest_external_consent(conn: sqlite3.Connection, user_id: int) -> Optional[str]:
    """Return most recent external consent status for a user."""
    row = conn.execute(
        "SELECT status FROM external_consent WHERE user_id=? ORDER BY timestamp DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    return row[0] if row else None