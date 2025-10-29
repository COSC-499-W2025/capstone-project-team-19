from src.db import connect, init_schema, get_or_create_user
from .token_store import get_github_token
from .github_api import list_user_repos

conn = connect()
init_schema(conn)

user_id = get_or_create_user(conn, "timmi")
token = get_github_token(conn, user_id)

repos = list_user_repos(token)

print("\nGitHub Repositories:")
for r in repos:
    print(" -", r)
