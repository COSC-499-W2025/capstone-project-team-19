
import sqlite3

def save_token_placeholder(conn: sqlite3.Connection, user_id: int):
    conn.execute("""
        INSERT OR IGNORE INTO user_tokens (user_id, provider, access_token)
        VALUES (?, 'github', 'PENDING_OAUTH')
    """, (user_id,))

    conn.commit()