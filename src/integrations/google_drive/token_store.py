"""
Google Drive token storage module.

Saves and retrieves Google Drive OAuth tokens from the user_tokens table
with provider='google_drive'. Mirrors src/integrations/github/token_store.py.

"""

from src.integrations.github.security.crypto_utils import encrypt_token, decrypt_token

PROVIDER = "google_drive"


def save_google_drive_tokens(conn, user_id, access_token, refresh_token=None, expires_at=None):
    """
    Save Google Drive OAuth tokens for a user.

    Encrypts both access_token and refresh_token before storing.
    If tokens already exist for this user, they are replaced (UPSERT).
    """
    _ensure_user_tokens_table(conn)

    encrypted_access = encrypt_token(access_token)
    encrypted_refresh = encrypt_token(refresh_token) if refresh_token else None

    conn.execute("""
        INSERT OR REPLACE INTO user_tokens (user_id, provider, access_token, refresh_token, expires_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, PROVIDER, encrypted_access, encrypted_refresh, expires_at))
    conn.commit()


def get_google_drive_token(conn, user_id):
    """
    Retrieve the stored Google Drive access token for a user.

    Returns the decrypted access_token string if found, otherwise None.
    """
    _ensure_user_tokens_table(conn)

    row = conn.execute("""
        SELECT access_token FROM user_tokens
        WHERE user_id = ? AND provider = ?
    """, (user_id, PROVIDER)).fetchone()

    return decrypt_token(row[0]) if row else None


def get_google_drive_refresh_token(conn, user_id):
    """
    Retrieve the stored Google Drive refresh token for a user.

    Returns the decrypted refresh_token string if found, otherwise None.
    """
    _ensure_user_tokens_table(conn)

    row = conn.execute("""
        SELECT refresh_token FROM user_tokens
        WHERE user_id = ? AND provider = ?
    """, (user_id, PROVIDER)).fetchone()

    if not row or not row[0]:
        return None
    return decrypt_token(row[0])


def revoke_google_drive_tokens(conn, user_id):
    """
    Remove stored Google Drive tokens for a user.
    """
    conn.execute("""
        DELETE FROM user_tokens
        WHERE user_id = ? AND provider = ?
    """, (user_id, PROVIDER))
    conn.commit()


def _ensure_user_tokens_table(conn):
    """
    Ensure the user_tokens table exists.
    Called automatically by save/get functions to avoid crashes.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            provider TEXT NOT NULL,
            access_token TEXT,
            refresh_token TEXT,
            expires_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, provider)
        )
    """)
    conn.commit()
