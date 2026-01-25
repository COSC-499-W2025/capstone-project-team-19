import time
import pytest
import jwt as pyjwt  # pyjwt library

from src.api.auth.security import (
    _truncate_password_for_bcrypt,
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    JWT_ALGORITHM,
)

def test_truncate_password_no_change_when_short():
    pw = "pw123"
    assert _truncate_password_for_bcrypt(pw) == pw

def test_truncate_password_ascii_truncates_to_max_72_bytes():
    pw = "a" * 200
    truncated = _truncate_password_for_bcrypt(pw)
    assert len(truncated.encode("utf-8")) <= 72
    assert truncated == "a" * 72  # ASCII = 1 byte each

def test_hash_and_verify_password_success():
    pw = "correct horse battery staple"
    pw_hash = hash_password(pw)
    assert isinstance(pw_hash, str)
    assert verify_password(pw, pw_hash) is True

def test_verify_password_fails_for_wrong_password():
    pw_hash = hash_password("pw123")
    assert verify_password("wrong", pw_hash) is False

def test_long_password_does_not_crash_and_is_verifiable():
    pw = "a" * 500
    h = hash_password(pw)
    assert verify_password(pw, h) is True

def test_hash_and_verify_long_password_consistent_due_to_truncation():
    # Two different long passwords that share the first 72 bytes should behave the same
    base = "a" * 72
    pw1 = base + "X" * 100
    pw2 = base + "Y" * 100

    h = hash_password(pw1)

    # Because you truncate before hashing/verifying, pw2 should verify too
    assert verify_password(pw2, h) is True

def test_create_and_decode_access_token_roundtrip():
    token = create_access_token(secret="test-secret", user_id=123, username="alice", expires_minutes=60)
    payload = decode_access_token(secret="test-secret", token=token)

    assert payload["sub"] == "123"
    assert payload["username"] == "alice"
    assert "iat" in payload
    assert "exp" in payload

def test_decode_access_token_raises_with_wrong_secret():
    token = create_access_token(secret="test-secret", user_id=1, username="alice", expires_minutes=60)
    with pytest.raises(pyjwt.PyJWTError):
        decode_access_token(secret="wrong-secret", token=token)

def test_decode_access_token_raises_when_expired():
    token = create_access_token(secret="test-secret", user_id=1, username="alice", expires_minutes=0)

    # Sleep to ensure exp < now (some systems have 1s granularity)
    time.sleep(1)

    with pytest.raises(pyjwt.ExpiredSignatureError):
        decode_access_token(secret="test-secret", token=token)