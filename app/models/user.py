from sqlalchemy import BigInteger, Boolean, Column, DateTime, String, func
from app.config.database import Base


class User(Base):
    """SQLAlchemy model for user creation and authentication"""

    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True, index=True)

    username = Column(String(20), nullable=False, unique=True, index=True)
    password = Column(String(150), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
