"""
database.py – Async SQLAlchemy engine and session factory.
"""

import re
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings

def _get_engine_url():
    """
    Constructs the database URL safely. 
    It bypasses the buggy URL parsing by using SQLAlchemy's URL.create
    when DB_USER and DB_PASSWORD are provided.
    """
    original_url = settings.DATABASE_URL
    
    if settings.DB_USER and settings.DB_PASSWORD:
        # Regex to extract host, port, and database name from:
        # postgresql+asyncpg://[ANY_STUFF]@host:port/dbname
        # We look for the part after the last '@'
        match = re.search(r"@?([^/:]+)(?::(\d+))?/([^?#]+)", original_url)
        if match:
            host = match.group(1)
            port = int(match.group(2)) if match.group(2) else 5432
            database = match.group(3)
            
            return URL.create(
                drivername="postgresql+asyncpg",
                username=settings.DB_USER,
                password=settings.DB_PASSWORD,
                host=host,
                port=port,
                database=database
            )
    
    return original_url

def _get_connect_args():
    return {
        "statement_cache_size": 0,
        "command_timeout": 60
    }

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

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

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
