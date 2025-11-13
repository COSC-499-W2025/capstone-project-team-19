import pytest
import sqlite3

from src.db import init_schema, get_or_create_user
from src.integrations.github import token_store

@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    return conn

def test_save_and_get_token(monkeypatch, conn):
    monkeypatch.setattr(token_store, "encrypt_token", lambda x: f"ENC({x})")
    monkeypatch.setattr(token_store, "decrypt_token", lambda x: x.replace("ENC(", "").replace(")", ""))

    user = get_or_create_user(conn, "Pink Floyd")
    token_store.save_github_token(conn, user, "testtoken123")
    assert token_store.get_github_token(conn, user) == "testtoken123"

def test_overwrite_token(monkeypatch, conn):
    monkeypatch.setattr(token_store, "encrypt_token", lambda x: f"ENC({x})")
    monkeypatch.setattr(token_store, "decrypt_token", lambda x: x.replace("ENC(", "").replace(")", ""))

    user = get_or_create_user(conn, "Alice Chains")
    token_store.save_github_token(conn, user, "oldtoken")
    token_store.save_github_token(conn, user, "newtoken")
    assert token_store.get_github_token(conn, user) == "newtoken"

def test_tokens_are_user_isolated(monkeypatch, conn):
    monkeypatch.setattr(token_store, "encrypt_token", lambda x: f"ENC({x})")
    monkeypatch.setattr(token_store, "decrypt_token", lambda x: x.replace("ENC(", "").replace(")", ""))

    u1 = get_or_create_user(conn, "Led Zeppelin")
    u2 = get_or_create_user(conn, "Lynyrd Skynyrd")

    token_store.save_github_token(conn, u1, "token1")
    token_store.save_github_token(conn, u2, "token2")

    assert token_store.get_github_token(conn, u1) == "token1"
    assert token_store.get_github_token(conn, u2) == "token2"

def test_mask_token():
    assert token_store.mask_token("1234567890") == "1234****7890"
    assert token_store.mask_token("abcdefghi") == "*********"
    assert token_store.mask_token("") == ""

def test_revoke_token(monkeypatch, conn):
    monkeypatch.setattr(token_store, "encrypt_token", lambda x: f"ENC({x})")
    monkeypatch.setattr(token_store, "decrypt_token", lambda x: x.replace("ENC(", "").replace(")", ""))

    user = get_or_create_user(conn, "Brandon Flowers")
    token_store.save_github_token(conn, user, "deletetoken")
    token_store.revoke_github_token(conn, user)

    assert token_store.get_github_token(conn, user) is None
