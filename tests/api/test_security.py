"""Tests for security.py functions."""
import pytest
import jwt
from datetime import datetime, timedelta, timezone
from src.api.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    JWT_ALGORITHM
)

class TestPasswordHashing:
    def test_hash_password_creates_hash(self):
        """Password hashing should create a hash different from original."""
        password = "testpass123"
        hash1 = hash_password(password)
        assert hash1 != password
        assert len(hash1) > 20  # Argon2 hashes are long
    
    def test_hash_password_different_each_time(self):
        """Same password should produce different hashes (salt)."""
        password = "testpass123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2  # Different salts
    
    def test_verify_password_correct(self):
        """Verify password should return True for correct password."""
        password = "testpass123"
        password_hash = hash_password(password)
        assert verify_password(password, password_hash) is True
    
    def test_verify_password_incorrect(self):
        """Verify password should return False for incorrect password."""
        password = "testpass123"
        wrong_password = "wrongpass"
        password_hash = hash_password(password)
        assert verify_password(wrong_password, password_hash) is False
    
    def test_verify_password_empty(self):
        """Empty password should be handled."""
        password = ""
        password_hash = hash_password(password)
        assert verify_password(password, password_hash) is True
        assert verify_password("notempty", password_hash) is False

class TestJWTCreation:
    def test_create_access_token_valid(self):
        """Create access token should return valid JWT."""
        secret = "test-secret"
        token = create_access_token(secret=secret, user_id=1, username="testuser")
        assert isinstance(token, str)
        assert len(token) > 20
    
    def test_create_access_token_contains_payload(self):
        """Token should contain user_id and username."""
        secret = "test-secret"
        user_id = 42
        username = "testuser"
        token = create_access_token(secret=secret, user_id=user_id, username=username)
        
        decoded = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        assert decoded["sub"] == str(user_id)
        assert decoded["username"] == username
        assert "iat" in decoded
        assert "exp" in decoded
    
    def test_create_access_token_expires(self):
        """Token should have expiration time."""
        secret = "test-secret"
        token = create_access_token(secret=secret, user_id=1, username="testuser", expires_minutes=60)
        decoded = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        
        now = datetime.now(timezone.utc).timestamp()
        exp = decoded["exp"]
        assert exp > now
        assert exp <= now + 3600 + 5  # 60 minutes + small buffer
    
    def test_create_access_token_custom_expiry(self):
        """Token should respect custom expiration."""
        secret = "test-secret"
        token = create_access_token(secret=secret, user_id=1, username="testuser", expires_minutes=5)
        decoded = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        
        now = datetime.now(timezone.utc).timestamp()
        exp = decoded["exp"]
        assert exp <= now + 300 + 5  # 5 minutes + buffer

class TestJWTDecoding:
    def test_decode_access_token_valid(self):
        """Decode should work for valid token."""
        secret = "test-secret"
        token = create_access_token(secret=secret, user_id=1, username="testuser")
        payload = decode_access_token(secret=secret, token=token)
        assert payload["sub"] == "1"
        assert payload["username"] == "testuser"
    
    def test_decode_access_token_wrong_secret(self):
        """Decode should raise exception for wrong secret."""
        secret = "test-secret"
        token = create_access_token(secret=secret, user_id=1, username="testuser")
        with pytest.raises(jwt.PyJWTError):
            decode_access_token(secret="wrong-secret", token=token)
    
    def test_decode_access_token_expired(self):
        """Decode should raise exception for expired token."""
        secret = "test-secret"
        # Create expired token manually
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "1",
            "username": "testuser",
            "iat": int((now - timedelta(minutes=10)).timestamp()),
            "exp": int((now - timedelta(minutes=1)).timestamp())  # Expired 1 min ago
        }
        token = jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)
        
        with pytest.raises(jwt.ExpiredSignatureError):
            decode_access_token(secret=secret, token=token)
    
    def test_decode_access_token_invalid_format(self):
        """Decode should raise exception for invalid token."""
        secret = "test-secret"
        with pytest.raises(jwt.DecodeError):
            decode_access_token(secret=secret, token="not.a.valid.token")
