from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....schemas.auth import LoginRequest, TokenResponse
from ....config.database import get_db
from ....core.security import create_access_token, hash_password, verify_password
from ....models.user import User
from ....schemas.user import UserCreate, UserResponse


router = APIRouter()


@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""

    existing_user = db.query(User).filter(
        User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Username already registered!")

    hashed_password = hash_password(user_data.password)

    new_user = User(username=user_data.username, password=hashed_password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post('/login', response_model=TokenResponse)
def login_user(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login & get access token"""

    user = db.query(User).filter(User.username == credentials.username).first()

    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials!",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive!",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(access_token=token)
