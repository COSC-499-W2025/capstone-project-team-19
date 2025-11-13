from .security.crypto_utils import encrypt_token, decrypt_token

def save_github_token(conn, user_id, token):
    """
    The token is saved in the `user_tokens` table and associated with the given user_id. 
    If a GitHub token already exists for this user, it is replaced. 
    This allows future authenticated GitHub API calls without requiring the user to re-authorize.
    """
    _ensure_user_tokens_table(conn)

    encrypted = encrypt_token(token)

    conn.execute("""
        INSERT OR REPLACE INTO user_tokens (user_id, provider, access_token)
        VALUES (?, 'github', ?)
    """, (user_id, encrypted))
    conn.commit()


def get_github_token(conn, user_id):
    """
    Retrieve the stored GitHub OAuth token for a user.

    Looks up the most recent GitHub access token associated with the given user_id. 
    Returns the token string if found, otherwise None.
    """

    _ensure_user_tokens_table(conn)

    row = conn.execute("""
        SELECT access_token FROM user_tokens
        WHERE user_id=? AND provider='github'
    """, (user_id,)).fetchone()

    return decrypt_token(row[0]) if row else None

# if token is ever printed, mask it so the full token is not printed
def mask_token(token: str) -> str:
    if len(token) <= 9:
        return "*" * len(token)
    
    return token[:4] + "****" + token[-4:]

def revoke_github_token(conn, user_id):
    conn.execute("""
        DELETE FROM user_tokens
        WHERE user_id = ? AND provider = 'github'    
    """, (user_id,))

    conn.commit()
    print("GitHub token removed locally.")
    print("TO fully revoke GitHub access, visit: ")
    print("https://github.com/settings/applications")

def _ensure_user_tokens_table(conn):
    """
    Ensure the user_tokens table exists.
    Called automatically by save/get token functions to avoid crashes.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_tokens (
            user_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            access_token TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, provider)
        )
    """)
    conn.commit()