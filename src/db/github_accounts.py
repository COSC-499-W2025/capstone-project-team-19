"""
src/db/github_accounts.py

GitHub account-related database write operations:
 - Storing GitHub user account information
 - Verify if a user has a GitHub account
"""

import sqlite3


def store_github_account(conn, user_id, github_user):
    conn.execute("""
        INSERT OR REPLACE INTO github_accounts
        (user_id, github_username, github_id, github_name, github_email, github_profile_url)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id, github_user["login"], github_user["id"], github_user["name"], github_user["email"], github_user["profile_url"]
    ))
    conn.commit()

def has_github_account(conn: sqlite3.Connection, user_id: int) -> bool:
    """
    Return True if the user has at least one GitHub account linked.
    """
    row = conn.execute(
        """
        SELECT 1
        FROM github_accounts
        WHERE user_id = ?
        LIMIT 1
        """,
        (user_id,),
    ).fetchone()
    return row is not None
