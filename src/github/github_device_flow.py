import time
import requests
import os

"""
GitHub Device Authorization Flow (OAuth)

This module handles authentication with GitHub using the Device Flow, which is designed for CLI/desktop applications. 
It lets a user authenticate in the browser while this program polls GitHub for an access token. 
The token can then be used to call GitHub APIs on the user's behalf without exposing a client secret.
"""

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
DEVICE_CODE_URL = os.getenv("DEVICE_CODE_URL")
TOKEN_URL = os.getenv("TOKEN_URL")

def request_device_code(scope="repo"):
    # Get a device & user code from GitHub to start Device Flow.
    
    data = {
        "client_id": GITHUB_CLIENT_ID,
        "scope": scope
    }

    headers = {"Accept": "application/json"}

    try:
        r = requests.post(DEVICE_CODE_URL, data=data, headers=headers)
    except Exception as e:
        print(f"[GitHub] Network error while requesting device code: {e}")
        return None

    if r.status_code != 200:
        print(f"[GitHub] Failed to request device code: {r.text}")
        return None

    return r.json()

def poll_for_token(device_code: str, interval: int):
    # Poll GitHub until user logs in + we receive access token.

    if not device_code:
        print("[GitHub] No device code, cannot poll.")
        return None
    
    data = {
        "client_id": GITHUB_CLIENT_ID,
        "device_code": device_code,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
    }

    headers = {"Accept": "application/json"}

    while True:
        r = requests.post(TOKEN_URL, data=data, headers=headers)
        resp = r.json()

        if "access_token" in resp:
            return resp["access_token"]

        if resp.get("error") == "authorization_pending":
            time.sleep(interval)
            continue

        print(f"[GitHub] OAuth error: {resp}")
        return None
