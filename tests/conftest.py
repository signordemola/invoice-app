"""Test configuration and fixtures."""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.database import Base


TEST_DATABASE_URL = 'sqlite:///./test.db'

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["TESTING"] = "1"


engine = create_engine(TEST_DATABASE_URL, connect_args={
                       'check_same_thread': False})

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh db session for each test"""

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
