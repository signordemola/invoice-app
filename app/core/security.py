from datetime import datetime, timezone, timedelta
import secrets
from typing import Any, Dict, Optional, Tuple

import jwt
from pwdlib import PasswordHash

from ..config.settings import settings

password_hash = PasswordHash.recommended()
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def _create_token(
    data: Dict[str, Any],
    token_type: str,
    expires_minutes: int,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT token with a token-type claim."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)

    to_encode.update({"exp": expire, "type": token_type})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    return _create_token(
        data=data,
        token_type=ACCESS_TOKEN_TYPE,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRATION,
        expires_delta=expires_delta,
    )


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT refresh token with longer expiration."""
    return _create_token(
        data=data,
        token_type=REFRESH_TOKEN_TYPE,
        expires_minutes=settings.REFRESH_TOKEN_EXPIRATION,
        expires_delta=expires_delta,
    )


def _decode_token(token: str) -> Dict[str, Any] | None:
    """Decode a JWT token and return its payload if valid."""
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_access_token(token: str) -> str | None:
    """Verify a JWT access token and extract the user identifier."""
    payload = _decode_token(token)
    if not payload:
        return None

    token_type = payload.get("type")
    if token_type not in {None, ACCESS_TOKEN_TYPE}:
        return None

    user_id: str = payload.get("sub")
    return user_id


def verify_refresh_token(token: str) -> str | None:
    """Verify a JWT refresh token and extract the user identifier."""
    payload = _decode_token(token)
    if not payload or payload.get("type") != REFRESH_TOKEN_TYPE:
        return None

    user_id: str = payload.get("sub")
    return user_id


def generate_verification_token() -> Tuple[str, datetime]:
    """Generate a secure random token for email verification with expiration."""
    
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS
    )
    return token, expires_at


def generate_password_reset_token() -> Tuple[str, datetime]:
    """Generate a secure random token for password reset with expiration."""

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.PASSWORD_RESET_TOKEN_EXPIRATION_MINUTES
    )
    return token, expires_at
