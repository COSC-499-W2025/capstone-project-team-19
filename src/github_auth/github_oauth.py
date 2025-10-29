import webbrowser
from .github_device_flow import request_device_code, poll_for_token
from .token_store import save_github_token
from src.db import get_or_create_user

"""
Handles GitHub authentication using the Device OAuth flow.

Launches the GitHub device login process, opens the verification page in the user's browser, and waits for authorization.
Once the user is authorized, it retrieves the access token from GitHub and securely stores it in the local database, associated with the given username.
"""

def github_oauth(conn, username):
    print("\nGitHub Login Starting...")

    # request device code from GitHub
    auth = request_device_code(scope="repo read:user")

    print("\nGo to this page in your browser:")
    print(auth["verification_uri"])
    print(f"Enter this code: {auth['user_code']}\n")

    webbrowser.open(auth["verification_uri"])

    input("Press Enter after authorizing in GitHub...")

    # poll for token
    print("Waiting for GitHub authorization...")
    token = poll_for_token(auth["device_code"], auth["interval"])

    print("GitHub Authorized!")

    # save token in DB
    user_id = get_or_create_user(conn, username)
    save_github_token(conn, user_id, token)

    print("Token saved to database!")
    return token

if __name__ == "__main__":
    from src.db import connect, init_schema, get_or_create_user

    conn = connect()
    init_schema(conn)

    username = input("Enter your username (same one you use in the app): ").strip()
    if not username:
        username = "default"

    github_oauth(conn, username)
