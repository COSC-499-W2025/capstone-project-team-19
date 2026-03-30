import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.api.auth.routes as auth_routes

@pytest.fixture()
def app(monkeypatch):
    app = FastAPI()
    app.include_router(auth_routes.router)

    # override JWT secret dependency
    monkeypatch.setattr(auth_routes, "get_jwt_secret", lambda: "test-secret")

    # override DB dependency (not used if we mock db calls, but FastAPI will still resolve it)
    monkeypatch.setattr(auth_routes, "get_db", lambda: None)

    return app

@pytest.fixture()
def client(app):
    return TestClient(app)

def test_register_success(client, monkeypatch):
    # No existing user
    monkeypatch.setattr(auth_routes, "get_user_auth_by_username", lambda conn, username: None)

    # User creation returns new id
    monkeypatch.setattr(auth_routes, "create_user_with_password", lambda conn, username, email, pw_hash: 123)

    res = client.post("/auth/register", json={"username": "alice", "password": "Abcd1234"})
    assert res.status_code == 201
    data = res.json()
    assert data["user_id"] == 123
    assert data["username"] == "alice"

def test_register_rejects_weak_password_422(client, monkeypatch):
    # No existing user (validation should fail before DB call matters)
    monkeypatch.setattr(auth_routes, "get_user_auth_by_username", lambda conn, username: None)

    res = client.post("/auth/register", json={"username": "alice", "password": "abcde"})
    assert res.status_code == 422

def test_register_duplicate_username_400(client, monkeypatch):
    # Simulate username already existing
    monkeypatch.setattr(
        auth_routes,
        "get_user_auth_by_username",
        lambda conn, username: {"user_id": 1, "username": username, "hashed_password": "x"},
    )

    res = client.post("/auth/register", json={"username": "alice", "password": "Abcd1234"})
    assert res.status_code == 400
    assert res.json()["detail"] == "Username already taken"

def test_login_success_returns_jwt(client, monkeypatch):
    # Make password verification pass regardless of input
    monkeypatch.setattr(auth_routes, "verify_password", lambda password, hashed: True)

    # Simulate user record returned from DB
    fake_user = {
        "user_id": 7,
        "username": "alice",
        "hashed_password": "hashed",
    }
    monkeypatch.setattr(auth_routes, "get_user_auth_by_username", lambda conn, username: fake_user)

    res = client.post("/auth/login", json={"username": "alice", "password": "pw123"})
    assert res.status_code == 200

    body = res.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"

    # Validate token decodes with secret, and contains expected claims
    payload = jwt.decode(body["access_token"], "test-secret", algorithms=["HS256"])
    assert payload["username"] == "alice"
    assert payload["sub"] == "7" # create_access_token should set sub=str(user_id)

def test_login_invalid_credentials_401_when_user_missing(client, monkeypatch):
    monkeypatch.setattr(auth_routes, "get_user_auth_by_username", lambda conn, username: None)

    res = client.post("/auth/login", json={"username": "nope", "password": "pw"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid credentials"

def test_login_invalid_credentials_401_when_password_wrong(client, monkeypatch):
    fake_user = {"user_id": 7, "username": "alice", "hashed_password": "hashed"}
    monkeypatch.setattr(auth_routes, "get_user_auth_by_username", lambda conn, username: fake_user)

    monkeypatch.setattr(auth_routes, "verify_password", lambda password, hashed: False)

    res = client.post("/auth/login", json={"username": "alice", "password": "wrong"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid credentials"


# ── Delete account tests ──

@pytest.fixture()
def auth_app(monkeypatch):
    """App with auth router + dependency overrides for authenticated endpoints."""
    from src.api.dependencies import get_current_user_id, get_db

    _app = FastAPI()
    _app.include_router(auth_routes.router)

    monkeypatch.setattr(auth_routes, "get_jwt_secret", lambda: "test-secret")
    monkeypatch.setattr(auth_routes, "get_db", lambda: None)

    # Override the dependency so it returns a fixed user_id
    _app.dependency_overrides[get_current_user_id] = lambda: 7
    _app.dependency_overrides[get_db] = lambda: None

    return _app


@pytest.fixture()
def auth_client(auth_app):
    return TestClient(auth_app)


def test_delete_account_success(auth_client, monkeypatch):
    monkeypatch.setattr(auth_routes, "delete_user", lambda conn, user_id: True)

    res = auth_client.delete("/auth/delete-account")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True


def test_delete_account_user_not_found(auth_client, monkeypatch):
    monkeypatch.setattr(auth_routes, "delete_user", lambda conn, user_id: False)

    res = auth_client.delete("/auth/delete-account")
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found"


def test_delete_account_requires_auth(client):
    res = client.delete("/auth/delete-account")
    assert res.status_code in (401, 422)


# ── Logout tests ──

def test_logout_success(auth_client):
    res = auth_client.post("/auth/logout")

# ── Change password tests ──

def test_change_password_success(auth_client, monkeypatch):
    fake_user = {"user_id": 7, "username": "alice", "hashed_password": "hashed"}
    monkeypatch.setattr(auth_routes, "get_user_auth_by_id", lambda conn, user_id: fake_user)
    monkeypatch.setattr(auth_routes, "verify_password", lambda password, hashed: True)
    monkeypatch.setattr(auth_routes, "hash_password", lambda password: "new-hash")
    monkeypatch.setattr(auth_routes, "update_user_password", lambda conn, user_id, password_hash: True)

    res = auth_client.post(
        "/auth/change-password",
        json={"current_password": "OldPass123", "new_password": "NewPass123"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True


def test_logout_requires_auth(client):
    res = client.post("/auth/logout")

def test_change_password_wrong_current_password_400(auth_client, monkeypatch):
    fake_user = {"user_id": 7, "username": "alice", "hashed_password": "hashed"}
    monkeypatch.setattr(auth_routes, "get_user_auth_by_id", lambda conn, user_id: fake_user)
    monkeypatch.setattr(auth_routes, "verify_password", lambda password, hashed: False)

    res = auth_client.post(
        "/auth/change-password",
        json={"current_password": "WrongPass123", "new_password": "NewPass123"},
    )
    assert res.status_code == 400
    assert res.json()["detail"] == "Current password is incorrect"


def test_change_password_rejects_same_current_and_new_password_400(auth_client):
    res = auth_client.post(
        "/auth/change-password",
        json={"current_password": "SamePass123", "new_password": "SamePass123"},
    )
    assert res.status_code == 400
    assert res.json()["detail"] == "New password must be different from current password"


def test_change_password_rejects_weak_new_password_422(auth_client, monkeypatch):
    fake_user = {"user_id": 7, "username": "alice", "hashed_password": "hashed"}
    monkeypatch.setattr(auth_routes, "get_user_auth_by_id", lambda conn, user_id: fake_user)

    res = auth_client.post(
        "/auth/change-password",
        json={"current_password": "OldPass123", "new_password": "abc"},
    )
    assert res.status_code == 422


def test_change_password_requires_auth(client):
    res = client.post(
        "/auth/change-password",
        json={"current_password": "OldPass123", "new_password": "NewPass123"},
    )
    assert res.status_code in (401, 422)


# ── Integration test: real DB cascade ──

def test_delete_user_cascades_all_related_data():
    """Use a real in-memory SQLite DB to verify ON DELETE CASCADE works."""
    import sqlite3
    from pathlib import Path
    from src.db.users import delete_user

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    schema_path = Path(__file__).resolve().parents[2] / "src" / "db" / "schema" / "tables.sql"
    conn.executescript(schema_path.read_text())
    conn.execute("PRAGMA foreign_keys = ON")

    # Seed a user
    conn.execute(
        "INSERT INTO users (user_id, username, hashed_password) VALUES (1, 'alice', 'hash')"
    )
    # Seed a project owned by the user
    conn.execute(
        "INSERT INTO projects (project_key, user_id, display_name) VALUES (1, 1, 'my-proj')"
    )
    # Seed a project_version (the previously-broken FK)
    conn.execute(
        "INSERT INTO project_versions (version_key, project_key, fingerprint_strict) "
        "VALUES (1, 1, 'fp1')"
    )
    # Seed a token (user_tokens had no FK before)
    conn.execute(
        "INSERT INTO user_tokens (user_id, provider, access_token) VALUES (1, 'github', 'tok')"
    )
    # Seed consent rows
    conn.execute(
        "INSERT INTO external_consent (user_id, status, timestamp) VALUES (1, 'accepted', '2025-01-01')"
    )
    conn.commit()

    # Delete should succeed (would have failed before the cascade fixes)
    assert delete_user(conn, 1) is True

    # Verify everything is gone
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM project_versions").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM user_tokens").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM external_consent").fetchone()[0] == 0
