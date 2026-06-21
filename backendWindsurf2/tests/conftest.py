"""
conftest.py – Pytest configuration and fixtures.
"""

import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config import get_settings
from database import Base, get_db
from main import app

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Override settings for testing
@pytest.fixture(scope="session")
def test_settings():
    """Override settings for testing."""
    settings = get_settings()
    settings.DATABASE_URL = TEST_DATABASE_URL
    settings.DEBUG = True
    settings.SECRET_KEY = "test-secret-key-for-testing-only"
    return settings


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def client(test_db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    app.dependency_overrides[get_db] = lambda: test_db_session
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpassword123"
    }


@pytest.fixture
def sample_note_data():
    """Sample note data for testing."""
    return {
        "original_filename": "test_note.txt",
        "file_type": "text",
        "raw_text": "This is a test note with some content for quiz generation.",
        "cleaned_text": "This is a test note with some content for quiz generation."
    }


@pytest.fixture
def sample_quiz_data():
    """Sample quiz data for testing."""
    return {
        "total_questions": 5,
        "mc_ratio": 0.8,
        "difficulty": "medium"
    }


@pytest.fixture
def test_user_id():
    """Generate test user ID."""
    return uuid.uuid4()


@pytest.fixture
def test_note_id():
    """Generate test note ID."""
    return uuid.uuid4()


@pytest.fixture
def test_quiz_id():
    """Generate test quiz ID."""
    return uuid.uuid4()


# Async test helper
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
