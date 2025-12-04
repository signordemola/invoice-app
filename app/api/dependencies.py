from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings

from ..core.security import verify_access_token
from ..models.user import User
from ..config.database import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_token_from_request(request: Request) -> str | None:
    """
        Extract JWT token from cookie or Authorization header.
        Priority: Cookie > Authorization header
   """

    token = request.cookies.get(settings.COOKIE_NAME)
    if token:
        return token

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "")

    return None


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency that validates JWT token and returns the authenticated user"""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required!",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = get_token_from_request(request)
    if not token:
        raise credentials_exception

    user_id = verify_access_token(token)
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    return user
