import logging
from fastapi import Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.core.exceptions import ConflictException, ForbiddenException, UnauthorizedException
from app.services.database import transaction_scope
from ..models.user import User
from ..core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)

logger = logging.getLogger(__name__)


def issue_auth_tokens(user: User) -> tuple[str, str]:
    """Create a fresh access/refresh token pair for the user."""
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return access_token, refresh_token


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Attach access and refresh cookies to the outgoing response."""
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=access_token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.access_cookie_max_age,
        path="/"
    )
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.refresh_cookie_max_age,
        path="/"
    )


def authenticate_user(username: str, password: str, db: Session) -> tuple[str, str, User]:
    """Authenticate user and return fresh auth tokens."""

    logger.info(f"Authentication attempt for username: {username}")

    user = db.query(User).filter(User.username == username).first()

    if not user:
        logger.warning(f"Authentication failed: User not found - {username}")
        raise UnauthorizedException(
            message="Invalid username or password",
            code="INVALID_CREDENTIALS"
        )

    if not verify_password(password, user.password):
        logger.warning(
            f"Authentication failed: Invalid password for {username}")
        raise UnauthorizedException(
            message="Invalid username or password",
            code="INVALID_CREDENTIALS"
        )

    if not user.is_active:
        logger.warning(f"Authentication failed: Inactive account - {username}")
        raise ForbiddenException(
            message="Account is inactive. Please contact support.",
            code="ACCOUNT_INACTIVE"
        )

    access_token, refresh_token = issue_auth_tokens(user)

    logger.info(f"Authentication successful for user: {username}")
    return access_token, refresh_token, user


def register_user(username: str, password: str, db: Session) -> User:
    """Register a new user account"""

    logger.info(f"Registration attempt for username: {username}")

    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        logger.warning(
            f"Registration failed: Username already exists - {username}")
        raise ConflictException(
            message="Username already registered",
            code="USERNAME_EXISTS"
        )

    hashed_password = hash_password(password)

    try:
        with transaction_scope(db) as session:
            new_user = User(
                username=username,
                password=hashed_password,
                is_active=True
            )
            session.add(new_user)

        logger.info(f"User registered successfully: {username}")
        return new_user

    except IntegrityError:
        logger.warning(
            f"Registration failed: Race condition for username - {username}")
        raise ConflictException(
            message="Username already registered",
            code="USERNAME_EXISTS"
        )


def logout_user(response: Response) -> None:
    """Clear authentication and CSRF cookies on the outgoing response."""
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/"
    )
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/"
    )
    response.delete_cookie(
        key=settings.CSRF_COOKIE_NAME,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/"
    )
