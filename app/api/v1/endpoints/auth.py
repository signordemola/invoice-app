from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.config import settings

from ....schemas.auth import LoginRequest
from ....config.database import get_db
from ....services.auth_service import AuthenticationError, InactiveAccountError, UserExistsError, login_user, logout_user, register_user
from ....models.user import User
from ....schemas.user import UserCreate, UserResponse


router = APIRouter()


@router.post('/login')
def login_route(response: Response, credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login & get access token"""

    try:
        token, user = login_user(
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
            "message": "Login successful!",
            "user": {
                "id": user.id,
                "username": user.username
            }
        }

    except AuthenticationError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"}
        )

    except InactiveAccountError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error)
        )


@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_route(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""

    try:
        new_user = register_user(
            username=user_data.username,
            password=user_data.password,
            db=db
        )
        return new_user

    except UserExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.post('/logout')
def logout_route():
    return logout_user()
