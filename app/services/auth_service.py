import logging
from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.core.exceptions import ConflictException, ForbiddenException, UnauthorizedException
from app.services.database import transaction_scope
from ..models.user import User
from ..core.security import hash_password, verify_password, create_access_token

logger = logging.getLogger(__name__)


def authenticate_user(username: str, password: str, db: Session) -> tuple[str, User]:
    """Authenticate user and return JWT token"""

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

    token = create_access_token(data={"sub": str(user.id)})

    logger.info(f"Authentication successful for user: {username}")
    return token, user


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


def logout_user() -> dict:
    """Clear the authentication cookie and log the user out."""

    response = JSONResponse(
        status_code=status.HTTP_204_NO_CONTENT, content=None)

    response.delete_cookie(
        key=settings.COOKIE_NAME,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="strict"
    )

    return {"message": "Logged out successfully!"}
