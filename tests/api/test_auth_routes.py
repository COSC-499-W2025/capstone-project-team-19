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