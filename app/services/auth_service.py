from sqlalchemy.orm import Session
from ..models.user import User
from ..core.security import hash_password, verify_password, create_access_token


class AuthServiceError(Exception):
    """Base exception for authentication service errors"""
    pass


class AuthenticationError(AuthServiceError):
    """Raised when user credentials are invalid"""
    pass


class InactiveAccountError(AuthServiceError):
    """Raised when user account is inactive"""
    pass


class UserExistsError(AuthServiceError):
    """Raised when attempting to register with existing username"""
    pass


def login_user(username: str, password: str, db: Session) -> str:
    """Authenticate user and return JWT token"""

    user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(password, user.password):
        raise AuthenticationError("Invalid credentials!")

    if user.is_active is False:
        raise InactiveAccountError("Account is inactive!")

    token = create_access_token(data={"sub": str(user.id)})
    return token


def register_user(username: str, password: str, db: Session) -> str:
    """Register a new user account"""

    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise UserExistsError("Username already registered!")

    hashed_password = hash_password(password)

    new_user = User(username=username, password=hashed_password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user
