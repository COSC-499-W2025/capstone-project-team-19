from datetime import datetime
import sqlite3

EXTERNAL_CONSENT_TEXT = """
================= EXTERNAL SERVICE CONSENT =================

This application may send some of your data to external services
(e.g. LLM ) to analyze your digital work artifacts.

Before continuing, please read the following terms:

Before continuing, please read the following terms:

• Using external services may send your files or content off your device.
• We have no control over what external services do with your data. 
  They may store, process, or use it according to their own policies.
• You may withdraw consent at any time, which will prevent future external analyses.
• Data already sent to external services cannot be recalled or deleted by this system.
• Declining consent will not prevent you from using the system locally. 
  Local analysis will still work with all basic features.

Do you consent to send your data to external services? (y/n):

=======================================================
"""

def record_external_consent(conn: sqlite3.Connection, status: str, when: datetime | None = None) -> int:
    """Insert external consent record into SQLite DB."""
    if status not in ("accepted", "rejected"):
        raise ValueError("status must be 'accepted' or 'rejected'")
    ts = (when or datetime.now()).isoformat()
    cur = conn.execute(
        "INSERT INTO external_consent (user_id, status, timestamp) VALUES (1, ?, ?)",
        (status, ts),
    )
    conn.commit()
    return cur.lastrowid

def get_external_consent() -> str:
    """Prompt user for external service consent until get a valid input."""
    print(EXTERNAL_CONSENT_TEXT)
    while True:
        ans = input(">>> ").strip().lower()
        if ans in ("y", "n"):
            return "accepted" if ans == "y" else "rejected"
        print("Please type 'y' for yes or 'n' for no:")

def record_external_consent(conn: sqlite3.Connection, status: str, user_id: int = 1, when: datetime | None = None) -> int:
    """Insert external consent record for the given user."""
    if status not in ("accepted", "rejected"):
        raise ValueError("status must be 'accepted' or 'rejected'")
    ts = (when or datetime.now()).isoformat()
    cur = conn.execute(
        "INSERT INTO external_consent (user_id, status, timestamp) VALUES (?, ?, ?)",
        (user_id, status, ts),
    )
    conn.commit()
    return cur.lastrowid