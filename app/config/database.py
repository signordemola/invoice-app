import os
import time
from typing import Generator
from sqlalchemy import QueuePool, create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

from .settings import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=settings.POOL_SIZE,
    max_overflow=settings.MAX_OVERFLOW,
    pool_timeout=settings.POOL_TIMEOUT,
    pool_recycle=settings.POOL_RECYCLE,
    poolclass=QueuePool,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

def init_db() -> None:
    """Initialize the database by creating all tables."""

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a DB session with automatic retry on connection failures."""

    attempts = 0
    max_attempts = 3
    backoff_time = 0.5

    while True:
        try:
            db = SessionLocal()
            break
        except Exception as e:
            attempts += 1
            if attempts >= max_attempts:
                raise
            time.sleep(backoff_time)
            backoff_time *= 2

    try:
        yield db
    finally:
        db.close()


if not os.getenv("TESTING"):
    init_db()