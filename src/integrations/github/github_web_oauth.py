import requests
import os
from urllib.parse import urlencode

"""
GitHub Web OAuth Flow (Authorization Code Flow)

This module handles authentication with GitHub using the Authorization Code Flow,
which is designed for web applications and APIs. It generates authorization URLs
and exchanges authorization codes for access tokens.
"""

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/auth/github/callback")
TOKEN_URL = os.getenv("TOKEN_URL", "https://github.com/login/oauth/access_token")
AUTHORIZE_URL = "https://github.com/login/oauth/authorize"


def generate_github_auth_url(state: str = None, scope: str = "repo read:user read:org") -> str:
    """
    Generate a GitHub OAuth authorization URL for the web flow.
    """
    if not GITHUB_CLIENT_ID:
        raise ValueError("GITHUB_CLIENT_ID environment variable is not set")
    
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "scope": scope,
    }
    
    if state:
        params["state"] = state
    
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code_for_token(code: str, state: str = None) -> dict:
    """
    Exchange an authorization code for an access token.
    """
    if not GITHUB_CLIENT_ID:
        raise ValueError("GITHUB_CLIENT_ID environment variable is not set")
    if not GITHUB_CLIENT_SECRET:
        raise ValueError("GITHUB_CLIENT_SECRET environment variable is not set")
    
    data = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code,
    }
    
    if state:
        data["state"] = state
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    
    try:
        r = requests.post(TOKEN_URL, data=data, headers=headers)
    except Exception as e:
        print(f"[GitHub] Network error during token exchange: {e}")
        return None
    
    if r.status_code != 200:
        print(f"[GitHub] Failed to exchange code for token: {r.status_code} - {r.text}")
        return None
    
    response = r.json()
    
    if "error" in response:
        print(f"[GitHub] OAuth error: {response.get('error_description', response['error'])}")
        return None
    
    if "access_token" not in response:
        print(f"[GitHub] No access_token in response: {response}")
        return None
    
    return response