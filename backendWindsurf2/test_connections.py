import asyncio
from database import engine, get_db
from sqlalchemy import text
from services.auth_service import redis_client

async def test_all():
    global engine
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("Database connection SUCCESS")
    except Exception as e:
        print(f"Database connection FAILED: {e}")

    try:
        redis_client.ping()
        print("Redis connection SUCCESS")
    except Exception as e:
        print(f"Redis connection FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_all())
