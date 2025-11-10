import pytest, sqlite3, webbrowser, builtins

from src.github.github_oauth import github_oauth
from src.github.github_device_flow import request_device_code
from src.db import init_schema, get_or_create_user


@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    return conn

# testing overall flow, everything goes smoothly
def test_github_oauth_happy_path(monkeypatch, conn, capsys):
    fake_auth = {
        "verification_uri": "https://github.com/login/device",
        "user_code": "FAKECODE123",
        "device_code": "DEVICE123",
        "interval": 1,
    }

    # Patch request_device_code
    monkeypatch.setattr(
        "src.github.github_oauth.request_device_code",
        lambda scope: fake_auth,
    )

    # Capture browser open
    clicked = []
    monkeypatch.setattr(webbrowser, "open", lambda url: clicked.append(url))

    # Fake token polling
    monkeypatch.setattr(
        "src.github.github_oauth.poll_for_token",
        lambda d, i: "FAKE_TOKEN_ABC",
    )

    # Auto-press Enter
    monkeypatch.setattr(builtins, "input", lambda prompt="": "")

    # Fake DB save
    saved = {}
    def fake_save(conn_, user_id, token):
        saved["user_id"] = user_id
        saved["token"] = token

    monkeypatch.setattr(
        "src.github.github_oauth.save_github_token",
        fake_save
    )

    user = get_or_create_user(conn, "TestUser")

    token = github_oauth(conn, user)

    assert token == "FAKE_TOKEN_ABC"
    assert saved["user_id"] == user
    assert saved["token"] == "FAKE_TOKEN_ABC"
    assert clicked == ["https://github.com/login/device"]

    # Ensure masked output printed (not real token)
    output = capsys.readouterr().out
    assert "FAKE_TOKEN_ABC" not in output  
    assert "****" in output  

def test_github_oauth_request_device_code_fails(monkeypatch, conn):
    monkeypatch.setattr(
        "src.github.github_oauth.request_device_code",
        lambda scope: (_ for _ in ()).throw(RuntimeError("GitHub down")),
    )

    with pytest.raises(RuntimeError):
        github_oauth(conn, "User123")

# poll for token returns None (the user either denied or it timed out)
def test_github_oauth_poll_returns_none(monkeypatch, conn):
    fake_auth = {
        "verification_uri": "https://github.com/login/device",
        "user_code": "FAKE123",
        "device_code": "DEV123",
        "interval": 1,
    }

    monkeypatch.setattr("src.github.github_oauth.request_device_code", lambda s: fake_auth)
    monkeypatch.setattr("src.github.github_oauth.poll_for_token", lambda d, i: None)
    monkeypatch.setattr(webbrowser, "open", lambda u: None)
    monkeypatch.setattr(builtins, "input", lambda p="": "")

    with pytest.raises(Exception):
        github_oauth(conn, "User123")

# poll_for_token failes and causes an exception
def test_github_oauth_poll_raises(monkeypatch, conn):
    fake_auth = {
        "verification_uri": "https://github.com/login/device",
        "user_code": "FAKE123",
        "device_code": "DEV123",
        "interval": 1,
    }

    monkeypatch.setattr(
        "src.github.github_oauth.request_device_code",
        lambda *args, **kwargs: fake_auth
    )
    monkeypatch.setattr(
        "src.github.github_oauth.poll_for_token",
        lambda d,i: (_ for _ in ()).throw(RuntimeError("Auth expired")),
    )
    monkeypatch.setattr(webbrowser, "open", lambda u: None)
    monkeypatch.setattr(builtins, "input", lambda p="": "")

    response = request_device_code()
    assert response is None

# browser opening fails
def test_github_oauth_browser_error(monkeypatch, conn):
    fake_auth = {
        "verification_uri": "https://github.com/login/device",
        "user_code": "FAKE123",
        "device_code": "DEV123",
        "interval": 1,
    }

    monkeypatch.setattr(
        "src.github.github_oauth.request_device_code",
        lambda *args, **kwargs: fake_auth
    )
    monkeypatch.setattr(webbrowser, "open", lambda u: (_ for _ in ()).throw(OSError("no browser")))
    monkeypatch.setattr("src.github.github_oauth.poll_for_token", lambda d,i: "FAKE")
    monkeypatch.setattr("src.github.github_oauth.save_github_token", lambda *args: None)
    monkeypatch.setattr(builtins, "input", lambda p="": "")

    token = github_oauth(conn, "TestUser")
    assert token == "FAKE"

# saving to DB fails
def test_github_oauth_save_fails(monkeypatch, conn):
    fake_auth = {
        "verification_uri": "https://github.com/login/device",
        "user_code": "FAKE123",
        "device_code": "DEV123",
        "interval": 1,
    }

    monkeypatch.setattr(
        "src.github.github_oauth.request_device_code",
        lambda *args, **kwargs: fake_auth
    )
    monkeypatch.setattr("src.github.github_oauth.poll_for_token", lambda d,i: "FAKE")
    monkeypatch.setattr(webbrowser, "open", lambda u: None)
    monkeypatch.setattr(builtins, "input", lambda p="": "")

    monkeypatch.setattr(
        "src.github.github_oauth.save_github_token",
        lambda *args: (_ for _ in ()).throw(RuntimeError("DB write fail"))
    )

    with pytest.raises(RuntimeError):
        github_oauth(conn, "TestUser")
