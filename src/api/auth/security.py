from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

JWT_ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def create_access_token(*, secret: str, user_id: int, username: str, expires_minutes: int = 60) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "username": username,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes = expires_minutes)).timestamp())
    }
    return jwt.encode(payload, secret, algorithms=[JWT_ALGORITHM])

def decode_access_token(*, secret: str, token: str) -> dict[str, Any]:
    # will raise exceptions if invalid/expired
    return jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
