from src.db import connect
from src.github.token_store import get_github_token

conn = connect()
user_id = 15  # whatever your test user is

token = get_github_token(conn, user_id)
print("Decrypted token:", token)
