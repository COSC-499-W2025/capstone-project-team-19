import time
import requests

GITHUB_CLIENT_ID = "Ov23li5mNKlRYVANwGac"

DEVICE_CODE_URL = "https://github.com/login/device/code"
TOKEN_URL = "https://github.com/login/oauth/access_token"


def request_device_code(scope="repo"):
    """
    Step 1: Get a device & user code from GitHub to start Device Flow.
    """
    data = {
        "client_id": GITHUB_CLIENT_ID,
        "scope": scope
    }

    headers = {"Accept": "application/json"}
    r = requests.post(DEVICE_CODE_URL, data=data, headers=headers)

    if r.status_code != 200:
        raise RuntimeError(f"Failed to request device code: {r.text}")

    return r.json()


def poll_for_token(device_code: str, interval: int):
    """
    Step 2: Poll GitHub until user logs in + we receive access token.
    """
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

        raise RuntimeError(f"OAuth error: {resp}")
