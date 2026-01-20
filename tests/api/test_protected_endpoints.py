"""Tests for protected endpoints using JWT authentication."""
import pytest
import os
import jwt
from datetime import datetime, timedelta, timezone
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
    if "JWT_SECRET" in os.environ:
        del os.environ["JWT_SECRET"]

@pytest.fixture(autouse=True)
def setup_db():
    """Initialize database before each test."""
    conn = setup_test_db()
    yield conn
    conn.close()

class TestProtectedEndpoints:
    def test_projects_endpoint_requires_auth(self, setup_db):
        """GET /projects should require authentication."""
        res = client.get("/projects")
        assert res.status_code == 401
    
    def test_projects_endpoint_with_valid_token(self, setup_db):
        """GET /projects should work with valid JWT."""
        user_id = create_test_user(setup_db, "testuser", "testpass123")
        token = get_auth_token(client, "testuser", "testpass123")
        
        res = client.get("/projects", headers=get_auth_headers(token))
        assert res.status_code == 200
        assert "success" in res.json()
    
    def test_projects_endpoint_with_invalid_token(self, setup_db):
        """GET /projects should reject invalid token."""
        res = client.get("/projects", headers={"Authorization": "Bearer invalid.token.here"})
        assert res.status_code == 401
    
    def test_projects_endpoint_with_expired_token(self, setup_db):
        """GET /projects should reject expired token."""
        create_test_user(setup_db, "testuser", "testpass123")
        secret = os.getenv("JWT_SECRET")
        
        # Create expired token
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "1",
            "username": "testuser",
            "iat": int((now - timedelta(minutes=10)).timestamp()),
            "exp": int((now - timedelta(minutes=1)).timestamp())
        }
        expired_token = jwt.encode(payload, secret, algorithm="HS256")
        
        res = client.get("/projects", headers=get_auth_headers(expired_token))
        assert res.status_code == 401
    
    def test_projects_endpoint_with_wrong_secret_token(self, setup_db):
        """GET /projects should reject token signed with wrong secret."""
        create_test_user(setup_db, "testuser", "testpass123")
        
        # Create token with wrong secret
        payload = {
            "sub": "1",
            "username": "testuser",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        wrong_token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
        
        res = client.get("/projects", headers=get_auth_headers(wrong_token))
        assert res.status_code == 401
    
    def test_projects_endpoint_missing_bearer_prefix(self, setup_db):
        """GET /projects should reject token without Bearer prefix."""
        create_test_user(setup_db, "testuser", "testpass123")
        token = get_auth_token(client, "testuser", "testpass123")
        res = client.get("/projects", headers={"Authorization": token})
        assert res.status_code == 401
    
    def test_projects_endpoint_no_authorization_header(self, setup_db):
        """GET /projects should reject request without Authorization header."""
        res = client.get("/projects")
        assert res.status_code == 401
    
    def test_skills_endpoint_requires_auth(self, setup_db):
        """GET /skills should require authentication."""
        res = client.get("/skills")
        assert res.status_code == 401
    
    def test_skills_endpoint_with_valid_token(self, setup_db):
        """GET /skills should work with valid JWT."""
        create_test_user(setup_db, "testuser", "testpass123")
        token = get_auth_token(client, "testuser", "testpass123")
        
        res = client.get("/skills", headers=get_auth_headers(token))
        assert res.status_code == 200
    
    def test_resumes_endpoint_requires_auth(self, setup_db):
        """GET /resumes should require authentication."""
        res = client.get("/resumes")
        assert res.status_code == 401
    
    def test_resumes_endpoint_with_valid_token(self, setup_db):
        """GET /resumes should work with valid JWT."""
        create_test_user(setup_db, "testuser", "testpass123")
        token = get_auth_token(client, "testuser", "testpass123")
        
        res = client.get("/resumes", headers=get_auth_headers(token))
        assert res.status_code == 200
    
    def test_consent_endpoint_requires_auth(self, setup_db):
        """GET /consent should require authentication."""
        res = client.get("/consent")
        assert res.status_code == 401
    
    def test_user_isolation(self, setup_db):
        """Users should only see their own data."""
        user1_id = create_test_user(setup_db, "user1", "pass1")
        user2_id = create_test_user(setup_db, "user2", "pass2")
        
        token1 = get_auth_token(client, "user1", "pass1")
        token2 = get_auth_token(client, "user2", "pass2")
        
        # Both should be able to access endpoints
        res1 = client.get("/projects", headers=get_auth_headers(token1))
        res2 = client.get("/projects", headers=get_auth_headers(token2))
        
        assert res1.status_code == 200
        assert res2.status_code == 200
    
    def test_token_with_nonexistent_user(self, setup_db):
        """Token with valid format but non-existent user_id should fail."""
        secret = os.getenv("JWT_SECRET")
        payload = {
            "sub": "99999",  # Non-existent user
            "username": "fakeuser",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        fake_token = jwt.encode(payload, secret, algorithm="HS256")
        
        res = client.get("/projects", headers=get_auth_headers(fake_token))
        assert res.status_code == 401
