"""
database.py – Async SQLAlchemy engine and session factory.
"""

from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from config import settings


def _get_engine_url():
    """Construct the SQLAlchemy database URL using explicit credentials when available."""
    original_url = settings.DATABASE_URL
    auth_user = settings.SUPABASE_AUTH_USER or settings.DB_USER
    auth_pass = settings.SUPABASE_AUTH_PASS or settings.DB_PASSWORD

    if not original_url:
        raise ValueError(
            "DATABASE_URL is not configured. Set DATABASE_URL in your environment variables."
        )

    try:
        parsed_url = make_url(original_url)
    except Exception as exc:
        raise ValueError(
            "DATABASE_URL is invalid. Use the format: postgresql+asyncpg://HOST:PORT/DATABASE"
        ) from exc

    if not parsed_url.host:
        raise ValueError(
            "DATABASE_URL must include a valid host. Example: "
            "postgresql+asyncpg://aws-1-eu-central-1.pooler.supabase.com:6543/postgres"
        )

    if auth_user and auth_pass:
        return URL.create(
            drivername=parsed_url.drivername or "postgresql+asyncpg",
            username=auth_user,
            password=auth_pass,
            host=parsed_url.host,
            port=parsed_url.port or 5432,
            database=parsed_url.database or "",
            query=parsed_url.query,
        )

    if auth_user or auth_pass:
        raise ValueError(
            "Both SUPABASE_AUTH_USER and SUPABASE_AUTH_PASS (or DB_USER and DB_PASSWORD) "
            "must be provided if either credential is set."
        )

    return original_url

def _get_connect_args():
    return {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "command_timeout": 60
    }

engine = create_async_engine(
    _get_engine_url(),
    echo=settings.DEBUG,
    poolclass=NullPool,
    connect_args=_get_connect_args(),
)

async_session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

def AsyncSessionLocal():
    return async_session_factory()

def get_task_engine():
    return create_async_engine(
        _get_engine_url(),
        echo=settings.DEBUG,
        poolclass=NullPool,
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
