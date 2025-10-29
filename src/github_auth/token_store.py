def save_github_token(conn, user_id, token):
    conn.execute("""
        INSERT OR REPLACE INTO user_tokens (user_id, provider, access_token)
        VALUES (?, 'github', ?)
    """, (user_id, token))
    conn.commit()


def get_github_token(conn, user_id):
    row = conn.execute("""
        SELECT access_token FROM user_tokens
        WHERE user_id=? AND provider='github'
    """, (user_id,)).fetchone()

    return row[0] if row else None
