"""
Tests to verify that protected endpoints require JWT authentication.

These tests ensure:
1. Endpoints reject requests without Authorization header (401)
2. Endpoints accept requests with valid JWT tokens
3. Auth enforcement doesn't break existing endpoint behavior
"""

import pytest
import jwt
from datetime import datetime, timedelta, timezone

from src.api.auth.security import create_access_token
from .conftest import TEST_JWT_SECRET
import src.db as db


def make_valid_token(user_id: int, username: str) -> str:
    """Create a valid JWT token for testing."""
    return create_access_token(
        secret=TEST_JWT_SECRET,
        user_id=user_id,
        username=username,
        expires_minutes=60,
    )


def make_expired_token(user_id: int, username: str) -> str:
    """Create an expired JWT token for testing."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": int((now - timedelta(minutes=10)).timestamp()),
        "exp": int((now - timedelta(minutes=1)).timestamp()),
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


class TestAuthRequiredOnGetEndpoints:
    """Verify GET endpoints require authentication."""

    def test_projects_endpoint_requires_auth(self, client):
        res = client.get("/projects")
        assert res.status_code == 401

    def test_projects_endpoint_with_valid_token(self, client, consent_user_id_1):
        token = make_valid_token(consent_user_id_1, "test-user")
        res = client.get("/projects", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200

    def test_projects_endpoint_with_expired_token(self, client, consent_user_id_1):
        token = make_expired_token(consent_user_id_1, "test-user")
        res = client.get("/projects", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401

    def test_projects_endpoint_with_invalid_token(self, client):
        res = client.get("/projects", headers={"Authorization": "Bearer invalid.token.here"})
        assert res.status_code == 401

    def test_projects_endpoint_missing_bearer_prefix(self, client, consent_user_id_1):
        token = make_valid_token(consent_user_id_1, "test-user")
        res = client.get("/projects", headers={"Authorization": token})
        assert res.status_code == 401

    def test_skills_endpoint_requires_auth(self, client):
        res = client.get("/skills")
        assert res.status_code == 401

    def test_skills_endpoint_with_valid_token(self, client, consent_user_id_1):
        token = make_valid_token(consent_user_id_1, "test-user")
        res = client.get("/skills", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200

    def test_resume_endpoint_requires_auth(self, client):
        res = client.get("/resume")
        assert res.status_code == 401

    def test_resume_endpoint_with_valid_token(self, client, consent_user_id_1):
        token = make_valid_token(consent_user_id_1, "test-user")
        res = client.get("/resume", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200


class TestAuthRequiredOnProtectedRoutes:
    """Verify various protected routes require authentication."""

    @pytest.mark.parametrize("method,path", [
        ("GET", "/projects"),
        ("GET", "/skills"),
        ("GET", "/resume"),
    ])
    def test_protected_endpoints_reject_unauthenticated_requests(self, client, method, path):
        res = client.request(method, path)
        assert res.status_code == 401

    @pytest.mark.parametrize("method,path", [
        ("GET", "/projects"),
        ("GET", "/skills"),
        ("GET", "/resume"),
    ])
    def test_protected_endpoints_accept_valid_token(self, client, method, path, consent_user_id_1):
        token = make_valid_token(consent_user_id_1, "test-user")
        res = client.request(method, path, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code != 401
        assert res.status_code in [200, 201, 204, 400, 404, 409, 422]

class TestTokenValidation:
    """Test token validation edge cases."""

    def test_token_with_wrong_secret(self, client, consent_user_id_1):
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(consent_user_id_1),
            "username": "test-user",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }
        wrong_token = jwt.encode(payload, "wrong-secret", algorithm="HS256")

        res = client.get("/projects", headers={"Authorization": f"Bearer {wrong_token}"})
        assert res.status_code == 401

    def test_token_with_nonexistent_user_id(self, client):
        token = make_valid_token(user_id=99999, username="nonexistent")
        res = client.get("/projects", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 404

    def test_empty_authorization_header(self, client):
        res = client.get("/projects", headers={"Authorization": ""})
        assert res.status_code == 401

    def test_malformed_bearer_header(self, client):
        res = client.get("/projects", headers={"Authorization": "Bearer "})
        assert res.status_code == 401

class TestMultipleUsers:
    """Test multiple users can authenticate (basic isolation sanity check)."""

    def test_user_isolation_different_tokens(self, client, seed_conn):
        from src.api.auth.security import hash_password
        pw_hash = hash_password("pass123")
        user1_id = db.users.create_user_with_password(seed_conn, "user1", None, pw_hash)
        user2_id = db.users.create_user_with_password(seed_conn, "user2", None, pw_hash)
        seed_conn.commit()

        token1 = make_valid_token(user1_id, "user1")
        token2 = make_valid_token(user2_id, "user2")

        res1 = client.get("/projects", headers={"Authorization": f"Bearer {token1}"})
        res2 = client.get("/projects", headers={"Authorization": f"Bearer {token2}"})

        assert res1.status_code == 200
        assert res2.status_code == 200

        payload1 = jwt.decode(token1, TEST_JWT_SECRET, algorithms=["HS256"])
        payload2 = jwt.decode(token2, TEST_JWT_SECRET, algorithms=["HS256"])

        assert payload1["sub"] == str(user1_id)
        assert payload2["sub"] == str(user2_id)
        assert payload1["username"] != payload2["username"]