def save_github_token(conn, user_id, token):
    """
    The token is saved in the `user_tokens` table and associated with the given user_id. 
    If a GitHub token already exists for this user, it is replaced. 
    This allows future authenticated GitHub API calls without requiring the user to re-authorize.
    """

    conn.execute("""
        INSERT OR REPLACE INTO user_tokens (user_id, provider, access_token)
        VALUES (?, 'github', ?)
    """, (user_id, token))
    conn.commit()


def get_github_token(conn, user_id):
    """
    Retrieve the stored GitHub OAuth token for a user.

    Looks up the most recent GitHub access token associated with the given user_id. 
    Returns the token string if found, otherwise None.
    """

    row = conn.execute("""
        SELECT access_token FROM user_tokens
        WHERE user_id=? AND provider='github'
    """, (user_id,)).fetchone()

    return row[0] if row else None
