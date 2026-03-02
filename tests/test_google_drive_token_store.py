import pytest
import sqlite3

from src.db import init_schema, get_or_create_user
from src.integrations.google_drive import token_store

@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    return conn

def _patch_crypto(monkeypatch):
    """Mock encrypt/decrypt so tests don't need a real Fernet key on disk."""
    monkeypatch.setattr(token_store, "encrypt_token", lambda x: f"ENC({x})")
    monkeypatch.setattr(token_store, "decrypt_token", lambda x: x.replace("ENC(", "").replace(")", ""))


def test_save_and_get_access_token(monkeypatch, conn):
    """Save a Google Drive token and retrieve it."""
    _patch_crypto(monkeypatch)
    user = get_or_create_user(conn, "Test User")

    token_store.save_google_drive_tokens(conn, user, "access123")
    assert token_store.get_google_drive_token(conn, user) == "access123"


def test_save_and_get_refresh_token(monkeypatch, conn):
    """Save both access and refresh tokens, retrieve the refresh token."""
    _patch_crypto(monkeypatch)
    user = get_or_create_user(conn, "Test User")

    token_store.save_google_drive_tokens(conn, user, "access123", refresh_token="refresh456")
    assert token_store.get_google_drive_refresh_token(conn, user) == "refresh456"


def test_get_refresh_token_when_none(monkeypatch, conn):
    """Refresh token returns None when not stored."""
    _patch_crypto(monkeypatch)
    user = get_or_create_user(conn, "Test User")

    token_store.save_google_drive_tokens(conn, user, "access123")
    assert token_store.get_google_drive_refresh_token(conn, user) is None


def test_overwrite_tokens(monkeypatch, conn):
    """Saving new tokens replaces the old ones."""
    _patch_crypto(monkeypatch)
    user = get_or_create_user(conn, "Test User")

    token_store.save_google_drive_tokens(conn, user, "old_access", refresh_token="old_refresh")
    token_store.save_google_drive_tokens(conn, user, "new_access", refresh_token="new_refresh")

    assert token_store.get_google_drive_token(conn, user) == "new_access"
    assert token_store.get_google_drive_refresh_token(conn, user) == "new_refresh"


def test_tokens_are_user_isolated(monkeypatch, conn):
    """Different users have independent Google Drive tokens."""
    _patch_crypto(monkeypatch)
    u1 = get_or_create_user(conn, "User One")
    u2 = get_or_create_user(conn, "User Two")

    token_store.save_google_drive_tokens(conn, u1, "token_a", refresh_token="refresh_a")
    token_store.save_google_drive_tokens(conn, u2, "token_b", refresh_token="refresh_b")

    assert token_store.get_google_drive_token(conn, u1) == "token_a"
    assert token_store.get_google_drive_token(conn, u2) == "token_b"
    assert token_store.get_google_drive_refresh_token(conn, u1) == "refresh_a"
    assert token_store.get_google_drive_refresh_token(conn, u2) == "refresh_b"


def test_tokens_isolated_from_github(monkeypatch, conn):
    """Google Drive tokens don't interfere with GitHub tokens in the same table."""
    _patch_crypto(monkeypatch)
    user = get_or_create_user(conn, "Test User")

    # Insert a GitHub token directly
    conn.execute("""
        INSERT INTO user_tokens (user_id, provider, access_token)
        VALUES (?, 'github', ?)
    """, (user, "ENC(github_token)"))
    conn.commit()

    # Save a Google Drive token
    token_store.save_google_drive_tokens(conn, user, "drive_token")

    # Google Drive returns its own token, not GitHub's
    assert token_store.get_google_drive_token(conn, user) == "drive_token"

    # GitHub token is still there untouched
    row = conn.execute(
        "SELECT access_token FROM user_tokens WHERE user_id = ? AND provider = 'github'",
        (user,)
    ).fetchone()
    assert row is not None


def test_revoke_tokens(monkeypatch, conn):
    """Revoking removes the Google Drive tokens."""
    _patch_crypto(monkeypatch)
    user = get_or_create_user(conn, "Test User")

    token_store.save_google_drive_tokens(conn, user, "access123", refresh_token="refresh456")
    token_store.revoke_google_drive_tokens(conn, user)

    assert token_store.get_google_drive_token(conn, user) is None
    assert token_store.get_google_drive_refresh_token(conn, user) is None


def test_get_token_no_tokens_stored(monkeypatch, conn):
    """Returns None when no tokens have been saved for this user."""
    _patch_crypto(monkeypatch)
    user = get_or_create_user(conn, "Test User")

    assert token_store.get_google_drive_token(conn, user) is None
    assert token_store.get_google_drive_refresh_token(conn, user) is None


def test_save_with_expires_at(monkeypatch, conn):
    """The expires_at value is stored and retrievable."""
    _patch_crypto(monkeypatch)
    user = get_or_create_user(conn, "Test User")

    token_store.save_google_drive_tokens(conn, user, "access123", expires_at="2026-02-08T12:00:00")

    row = conn.execute(
        "SELECT expires_at FROM user_tokens WHERE user_id = ? AND provider = ?",
        (user, "google_drive")
    ).fetchone()
    assert row[0] == "2026-02-08T12:00:00"
