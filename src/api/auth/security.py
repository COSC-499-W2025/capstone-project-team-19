from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_ALGORITHM = "HS256"

def _truncate_password_for_bcrypt(password: str) -> str:
    """
    Truncate password to 72 bytes (bcrypt limit), ensuring we don't cut
    in the middle of a UTF-8 character.
    """
    password_bytes = password.encode('utf-8')
    if len(password_bytes) <= 72:
        return password
    
    # Truncate to 72 bytes, ensuring we don't cut in the middle of a UTF-8 character
    truncated_bytes = password_bytes[:72]
    # Remove any incomplete UTF-8 sequences at the end
    while truncated_bytes and truncated_bytes[-1] & 0b11000000 == 0b10000000:
        truncated_bytes = truncated_bytes[:-1]
    return truncated_bytes.decode('utf-8', errors='ignore')

def hash_password(password: str) -> str:
    # bcrypt has a 72-byte limit, so truncate if necessary
    password = _truncate_password_for_bcrypt(password)
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    # Apply the same truncation as in hash_password to ensure consistency
    password = _truncate_password_for_bcrypt(password)
    return pwd_context.verify(password, password_hash)

def create_access_token(*, secret: str, user_id: int, username: str, expires_minutes: int = 60) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "username": username,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes = expires_minutes)).timestamp())
    }
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)

def decode_access_token(*, secret: str, token: str) -> dict[str, Any]:
    # will raise exceptions if invalid/expired
    return jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
