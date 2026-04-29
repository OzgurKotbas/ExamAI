"""
database.py – Async SQLAlchemy engine and session factory.
"""

import re
import logging
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings

logger = logging.getLogger("main")

def _get_engine_url():
    """
    Constructs the database URL safely. 
    Forces the use of explicit DB_USER and DB_PASSWORD to avoid parsing bugs.
    """
    original_url = settings.DATABASE_URL
    user = settings.DB_USER
    password = settings.DB_PASSWORD
    
    if user and password:
        # Masked logging for debugging (only shows first 3 chars of user)
        logger.info(f"Connecting to DB using explicit credentials. User starts with: {user[:3]}...")
        
        # Regex to extract host, port, and database name
        match = re.search(r"@?([^/:]+)(?::(\d+))?/([^?#]+)", original_url)
        if match:
            host = match.group(1)
            port = int(match.group(2)) if match.group(2) else 5432
            database = match.group(3)
            
            # CRITICAL: Some Poolers need the dot to be URL encoded if passed in a string,
            # but URL.create handles this. We use the raw values here.
            return URL.create(
                drivername="postgresql+asyncpg",
                username=user,
                password=password,
                host=host,
                port=port,
                database=database
            )
        else:
            logger.error("Could not parse HOST/PORT from DATABASE_URL. Check Render settings.")
    else:
        logger.warning("DB_USER or DB_PASSWORD is EMPTY. Falling back to DATABASE_URL (This might fail with user 'postgres' error).")
    
    return original_url

def _get_connect_args():
    return {
        "statement_cache_size": 0,
        "command_timeout": 60
    }

# Create engine
engine = create_async_engine(
    _get_engine_url(),
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    connect_args=_get_connect_args(),
)

async_session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

def AsyncSessionLocal():
    return async_session_factory()

def get_task_engine():
    return create_async_engine(
        _get_engine_url(),
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        connect_args=_get_connect_args(),
    )

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db() -> None:
    await engine.dispose()
