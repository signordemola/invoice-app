from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....schemas.auth import LoginRequest, TokenResponse
from ....config.database import get_db
from ....services.auth_service import AuthenticationError, InactiveAccountError, UserExistsError, login_user, register_user
from ....models.user import User
from ....schemas.user import UserCreate, UserResponse


router = APIRouter()


@router.post('/login', response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login & get access token"""

    try:
        token = login_user(
            username=credentials.username,
            password=credentials.password,
            db=db
        )
        return TokenResponse(access_token=token)

    except AuthenticationError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"}
        )

    except InactiveAccountError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        )


@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
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
