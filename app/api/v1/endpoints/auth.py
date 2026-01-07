from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from ....schemas.auth import LoginRequest
from ....config.database import get_db
from ....services.auth_service import authenticate_user, logout_user, register_user
from ....models.user import User
from ....schemas.user import UserCreate, UserResponse


router = APIRouter()


@router.post('/login')
def login_route(response: Response, credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login & get access token"""

    token, user = authenticate_user(
        username=credentials.username,
        password=credentials.password,
        db=db
    )

    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.cookie_max_age,
        path="/"
    )

    return {
        "message": "Login successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "is_active": user.is_active
        }
    }


@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_route(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""

    new_user = register_user(
        username=user_data.username,
        password=user_data.password,
        db=db
    )

    return new_user


@router.post('/logout')
def logout_route():
    """Logout a user"""

    return logout_user()
