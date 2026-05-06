"""Password hashing + JWT helpers.

Tokens carry a `type` claim (`"access"` or `"refresh"`) so a refresh token
can never be silently substituted for an access token at a protected route.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Optional

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

TokenType = Literal["access", "refresh"]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _create_token(subject: Any, token_type: TokenType, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    to_encode = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(subject: Any, expires_delta: Optional[timedelta] = None) -> str:
    delta = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    return _create_token(subject, "access", delta)


def create_refresh_token(subject: Any, expires_delta: Optional[timedelta] = None) -> str:
    delta = expires_delta or timedelta(days=settings.refresh_token_expire_days)
    return _create_token(subject, "refresh", delta)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_token(token: str, expected_type: Optional[TokenType] = None) -> Optional[dict]:
    """Decode a JWT and validate its type claim.

    Returns the decoded payload on success, or None if the token is invalid,
    expired, or the token type does not match `expected_type` when provided.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.JWTError:
        return None

    if expected_type is not None and payload.get("type") != expected_type:
        return None
    return payload
