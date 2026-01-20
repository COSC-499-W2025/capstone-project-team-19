"""Tests for auth endpoints (/auth/register, /auth/login)."""
import pytest
import os
from fastapi.testclient import TestClient
from src.api.main import app
import src.db as db
from .test_auth_helpers import (
    create_test_user,
    setup_test_db,
    set_jwt_secret,
    get_auth_token,
    get_auth_headers
)

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_env():
    """Set JWT_SECRET before each test."""
    set_jwt_secret()
    yield
    # Cleanup if needed
    if "JWT_SECRET" in os.environ:
        del os.environ["JWT_SECRET"]

@pytest.fixture(autouse=True)
def setup_db():
    """Initialize database before each test."""
    conn = setup_test_db()
    yield conn
    conn.close()

class TestRegister:
    def test_register_success(self, setup_db):
        """Successful registration should return user_id and username."""
        res = client.post("/auth/register", json={
            "username": "newuser",
            "password": "securepass123"
        })
        assert res.status_code == 200
        data = res.json()
        assert "user_id" in data
        assert data["username"] == "newuser"
        assert isinstance(data["user_id"], int)
    
    def test_register_duplicate_username(self, setup_db):
        """Registering duplicate username should fail."""
        create_test_user(setup_db, "existinguser", "pass123")
        
        res = client.post("/auth/register", json={
            "username": "existinguser",
            "password": "otherpass"
        })
        assert res.status_code == 400
        assert "already taken" in res.json()["detail"].lower()
    
    def test_register_case_insensitive_username(self, setup_db):
        """Username should be case-insensitive for duplicates."""
        create_test_user(setup_db, "TestUser", "pass123")
        
        res = client.post("/auth/register", json={
            "username": "testuser",  # Different case
            "password": "pass123"
        })
        assert res.status_code == 400
    
    def test_register_missing_fields(self, setup_db):
        """Missing fields should return validation error."""
        res = client.post("/auth/register", json={"username": "user"})
        assert res.status_code == 422  # Validation error
        
        res = client.post("/auth/register", json={"password": "pass"})
        assert res.status_code == 422

class TestLogin:
    def test_login_success(self, setup_db):
        """Successful login should return access token."""
        create_test_user(setup_db, "testuser", "testpass123")
        
        res = client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 20
    
    def test_login_invalid_username(self, setup_db):
        """Login with non-existent username should fail."""
        res = client.post("/auth/login", json={
            "username": "nonexistent",
            "password": "anypass"
        })
        assert res.status_code == 401
        assert "invalid credentials" in res.json()["detail"].lower()
    
    def test_login_invalid_password(self, setup_db):
        """Login with wrong password should fail."""
        create_test_user(setup_db, "testuser", "correctpass")
        
        res = client.post("/auth/login", json={
            "username": "testuser",
            "password": "wrongpass"
        })
        assert res.status_code == 401
        assert "invalid credentials" in res.json()["detail"].lower()
    
    def test_login_case_insensitive_username(self, setup_db):
        """Login should work with case-insensitive username."""
        create_test_user(setup_db, "TestUser", "testpass123")
        
        res = client.post("/auth/login", json={
            "username": "testuser",  # Different case
            "password": "testpass123"
        })
        assert res.status_code == 200
        assert "access_token" in res.json()
    
    def test_login_token_is_valid_jwt(self, setup_db):
        """Login token should be valid JWT."""
        create_test_user(setup_db, "testuser", "testpass123")
        token = get_auth_token(client, "testuser", "testpass123")
        
        # Verify it's a valid JWT by decoding
        import jwt
        secret = os.getenv("JWT_SECRET")
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        assert decoded["username"] == "testuser"
        assert "sub" in decoded

class TestAuthFlow:
    def test_register_then_login(self, setup_db):
        """User should be able to register then login."""
        # Register
        res = client.post("/auth/register", json={
            "username": "flowuser",
            "password": "flowpass123"
        })
        assert res.status_code == 200
        user_id = res.json()["user_id"]
        
        # Login
        res = client.post("/auth/login", json={
            "username": "flowuser",
            "password": "flowpass123"
        })
        assert res.status_code == 200
        token = res.json()["access_token"]
        
        # Token should be valid
        assert len(token) > 20
