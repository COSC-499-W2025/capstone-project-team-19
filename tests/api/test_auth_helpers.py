"""Helper functions for auth testing."""
import os
from fastapi.testclient import TestClient
import src.db as db

def create_test_user(conn, username: str = "testuser", password: str = "testpass123") -> int:
    """Create a test user with password hash. Returns user_id."""
    from src.api.auth.security import hash_password
    password_hash = hash_password(password)
    user_id = db.users.create_user_with_password(conn, username, None, password_hash)
    return user_id

def get_auth_token(client: TestClient, username: str = "testuser", password: str = "testpass123") -> str:
    """Login and return access token."""
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]

def get_auth_headers(token: str) -> dict:
    """Return headers dict with Authorization bearer token."""
    return {"Authorization": f"Bearer {token}"}

def setup_test_db():
    """Initialize test database and return connection."""
    conn = db.connect()
    db.init_schema(conn)
    return conn

def set_jwt_secret(secret: str = "test-secret-key-for-testing"):
    """Set JWT_SECRET env var for testing."""
    os.environ["JWT_SECRET"] = secret
