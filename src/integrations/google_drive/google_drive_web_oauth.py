import requests
import os
from urllib.parse import urlencode

"""
Google Drive Web OAuth Flow (Authorization Code Flow)

This module handles authentication with Google Drive using the Authorization Code Flow,
which is designed for web applications and APIs. It generates authorization URLs
and exchanges authorization codes for access tokens (including refresh tokens).

Mirrors the pattern used in src/integrations/github/github_web_oauth.py.
"""

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

# Same scopes used by the existing CLI flow
SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]


def generate_google_auth_url(state: str = None) -> str:
    """
    Generate a Google OAuth authorization URL for the web flow.

    """
    if not GOOGLE_CLIENT_ID:
        raise ValueError("GOOGLE_CLIENT_ID environment variable is not set")

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }

    if state:
        params["state"] = state

    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code_for_tokens(code: str) -> dict:
    """
    Exchange an authorization code for access and refresh tokens.

    """
    if not GOOGLE_CLIENT_ID:
        raise ValueError("GOOGLE_CLIENT_ID environment variable is not set")
    if not GOOGLE_CLIENT_SECRET:
        raise ValueError("GOOGLE_CLIENT_SECRET environment variable is not set")

    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    try:
        r = requests.post(TOKEN_URL, data=data, headers=headers)
    except Exception as e:
        print(f"[Google Drive] Network error during token exchange: {e}")
        return None

    if r.status_code != 200:
        print(f"[Google Drive] Failed to exchange code for tokens: {r.status_code} - {r.text}")
        return None

    response = r.json()

    if "error" in response:
        print(f"[Google Drive] OAuth error: {response.get('error_description', response['error'])}")
        return None

    if "access_token" not in response:
        print(f"[Google Drive] No access_token in response: {response}")
        return None

    return response
