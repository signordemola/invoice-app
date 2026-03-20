from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.rate_limit import is_request_exempt, limiter
from app.core.security import verify_refresh_token
from ....schemas.auth import LoginRequest
from ....config.database import get_db
from ....models.user import User
from ....services.auth_service import (
    authenticate_user,
    issue_auth_tokens,
    logout_user,
    register_user,
    set_auth_cookies,
)
from ....schemas.user import UserCreate, UserResponse


router = APIRouter()


@router.post('/login')
@limiter.limit("5/minute", exempt_when=is_request_exempt)
def login_route(
    request: Request,
    response: Response,
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login & get access token"""

    access_token, refresh_token, user = authenticate_user(
        username=credentials.username,
        password=credentials.password,
        db=db
    )

    set_auth_cookies(response, access_token, refresh_token)

    return {
        "message": "Login successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "is_active": user.is_active
        }
    }


@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour", exempt_when=is_request_exempt)
def register_route(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""

    new_user = register_user(
        username=user_data.username,
        password=user_data.password,
        db=db
    )

    return new_user


@router.post('/refresh')
@limiter.limit("20/minute", exempt_when=is_request_exempt)
def refresh_route(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Rotate access and refresh tokens using the refresh-token cookie."""

    refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise UnauthorizedException(
            message="Refresh token is missing",
            code="REFRESH_TOKEN_MISSING"
        )

    user_id = verify_refresh_token(refresh_token)
    if user_id is None:
        raise UnauthorizedException(
            message="Refresh token is invalid or expired",
            code="INVALID_REFRESH_TOKEN"
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise UnauthorizedException(
            message="Refresh token is invalid or expired",
            code="INVALID_REFRESH_TOKEN"
        )

    if not user.is_active:
        raise ForbiddenException(
            message="Account is inactive. Please contact support.",
            code="ACCOUNT_INACTIVE"
        )

    access_token, new_refresh_token = issue_auth_tokens(user)
    set_auth_cookies(response, access_token, new_refresh_token)

    return {"message": "Token refreshed"}


@router.post('/logout')
@limiter.limit("20/minute", exempt_when=is_request_exempt)
def logout_route(request: Request, response: Response):
    """Logout a user"""

    logout_user(response)
    return {"message": "Logged out successfully!"}
