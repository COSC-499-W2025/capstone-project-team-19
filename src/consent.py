from datetime import datetime
import sqlite3

CONSENT_TEXT = """
================= USER CONSENT NOTICE =================

This application analyzes your local digital work artifacts (e.g.
documents, code repositories, notes, or media files) to help you gain
insights about your work contributions, creative processes, and project
evolution. The goal is to help you reflect on your productivity and
showcase your professional growth.

Before continuing, please read the following terms:

• All data processing occurs locally on your machine.
• No files or personal information are uploaded, shared, or transmitted.
• You may withdraw consent at any time by deleting your consent record
  or uninstalling the application.
• The system will access only directories or files that you explicitly
  select.
• Your consent status (Accepted or Rejected) and timestamp will be stored
  locally in a small SQLite database on your machine.

By typing “Y”, you give your consent for the application to analyze your
selected local files according to the description above.

Do you consent to continue? (y/n):

=======================================================
"""

def record_consent(conn: sqlite3.Connection, status: str, when: datetime | None = None) -> int:
    """Insert consent record with timestamp into SQLite DB."""
    if status not in ("accepted", "rejected"):
        raise ValueError("status must be 'accepted' or 'rejected'")
    ts = (when or datetime.now()).isoformat()
    cur = conn.execute(
        "INSERT INTO consent_log (user_id, status, timestamp) VALUES (1, ?, ?)",
        (status, ts),
    )
    conn.commit()
    return cur.lastrowid

def get_user_consent() -> str:
    """Prompt user for y/n input in the terminal."""
    while True:
        ans = input("Do you consent to continue? (y/n): ").strip().lower()
        if ans in ("y", "n"):
            return "accepted" if ans == "y" else "rejected"
        print("Please type 'y' for yes or 'n' for no:")