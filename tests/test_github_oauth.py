import pytest, sqlite3, webbrowser, builtins

from src.github_auth.github_oauth import github_oauth
from src.github_auth import token_store
from src.db import init_schema, get_or_create_user

@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    return conn

def test_github_oauth_flow(monkeypatch, conn):
    fake_auth = {
        "verification_uri": "https://github.com/login/device",
        "user_code": "FAKECODE123",
        "device_code": "DEVICE123",
        "interval": 1,
    }

    monkeypatch.setattr(
        "src.github_auth.github_oauth.request_device_code",
        lambda scope: fake_auth
    )

    clicked = []
    monkeypatch.setattr(webbrowser, "open", lambda url: clicked.append(url))
    monkeypatch.setattr(
        "src.github_auth.github_oauth.poll_for_token",
        lambda d, i: "FAKE_TOKEN_ABC"
    )
    monkeypatch.setattr(builtins, "input", lambda prompt="": "")

    saved = {}
    def fake_save(conn, uid, tok):
        saved["uid"] = uid
        saved["tok"] = tok

    monkeypatch.setattr(token_store, "save_github_token", fake_save)

    user = get_or_create_user(conn, "TestUser")
    result = github_oauth(conn, user)

    assert result == "FAKE_TOKEN_ABC"
    assert saved["uid"] == user
    assert saved["tok"] == "FAKE_TOKEN_ABC"
    assert clicked == ["https://github.com/login/device"]
