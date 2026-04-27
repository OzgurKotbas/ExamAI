"""
services/cache_service.py – Redis-backed quiz caching with a composite key.
"""

import hashlib
import json
import logging

import redis.asyncio as aioredis

from config import settings

logger = logging.getLogger(__name__)
_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get Redis connection instance."""
    global _redis
    if _redis is None:
        try:
            _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise ValueError("Failed to connect to Redis")
    return _redis


def _build_cache_key(user_id: str, note_id: str, total_questions: int, mc_ratio: float, difficulty: str, language: str = "tr") -> str:
    """Deterministic SHA-256 cache key (includes language for multilingual support)."""
    raw = f"{user_id}:{note_id}:{total_questions}:{mc_ratio:.2f}:{difficulty}:{language}"
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return f"quiz:cache:{digest}"


async def get_cached_quiz(
    user_id: str, note_id: str, total_questions: int, mc_ratio: float, difficulty: str, language: str = "tr"
) -> dict | None:
    """Get cached quiz if available."""
    try:
        redis = await get_redis()
        key = _build_cache_key(user_id, note_id, total_questions, mc_ratio, difficulty, language)
        raw = await redis.get(key)
        
        if raw:
            logger.info(f"Cache HIT for key: {key}")
            return json.loads(raw)
        
        logger.info(f"Cache MISS for key: {key}")
        return None
        
    except Exception as e:
        logger.error(f"Error getting cached quiz: {str(e)}")
        return None


async def set_cached_quiz(
    user_id: str, note_id: str, total_questions: int, mc_ratio: float, difficulty: str,
    quiz_id: str, ttl_seconds: int = 86400, language: str = "tr",
) -> str:
    """Store quiz_id under the cache key. Returns the cache key."""
    try:
        redis = await get_redis()
        key = _build_cache_key(user_id, note_id, total_questions, mc_ratio, difficulty, language)
        
        # Store the quiz payload
        await redis.setex(key, ttl_seconds, json.dumps({"quiz_id": quiz_id}))
        
        # Track the key under a per-user set so clear_user_cache can find it
        user_set_key = f"quiz:user_keys:{user_id}"
        await redis.sadd(user_set_key, key)
        await redis.expire(user_set_key, ttl_seconds)
        
        logger.info(f"Cache SET for key: {key}, quiz_id: {quiz_id}, TTL: {ttl_seconds}, lang: {language}")
        return key
        
    except Exception as e:
        logger.error(f"Error setting cached quiz: {str(e)}")
        raise ValueError("Failed to cache quiz")


async def invalidate_quiz_cache(
    user_id: str, note_id: str, total_questions: int, mc_ratio: float, difficulty: str
) -> None:
    """Invalidate cached quiz."""
    try:
        redis = await get_redis()
        key = _build_cache_key(user_id, note_id, total_questions, mc_ratio, difficulty)
        await redis.delete(key)
        logger.info(f"Cache DELETE for key: {key}")
        
    except Exception as e:
        logger.error(f"Error invalidating quiz cache: {str(e)}")


async def clear_user_cache(user_id: str) -> None:
    """Clear all cache entries for a specific user."""
    try:
        redis = await get_redis()
        user_set_key = f"quiz:user_keys:{user_id}"
        keys = await redis.smembers(user_set_key)
        if keys:
            await redis.delete(*keys)
            await redis.delete(user_set_key)
            logger.info(f"Cleared {len(keys)} cache entries for user: {user_id}")
    except Exception as e:
        logger.error(f"Error clearing user cache: {str(e)}")


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
        logger.info("Redis connection closed")
