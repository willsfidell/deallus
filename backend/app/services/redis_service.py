"""
Redis service for caching conversations and context.

Provides asynchronous Redis operations with TTL support for active conversation caching.
"""

import json
import logging
from typing import Optional, Any

import redis.asyncio as redis
from app.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Service for managing Redis cache operations."""

    _instance: Optional["RedisService"] = None
    _client: Optional[redis.Redis] = None
    _connection_string: str = ""

    @classmethod
    async def initialize(cls, redis_url: Optional[str] = None) -> "RedisService":
        """
        Initialize Redis client.

        Args:
            redis_url: Redis connection string. If None, uses settings.REDIS_URL

        Returns:
            RedisService instance
        """
        if cls._instance is not None:
            return cls._instance

        redis_url = redis_url or settings.REDIS_URL
        cls._connection_string = redis_url

        try:
            cls._client = await redis.from_url(redis_url, decode_responses=True)
            await cls._client.ping()
            logger.info(f"✅ Redis connected: {redis_url}")
        except Exception as e:
            logger.warning(
                f"⚠️ Redis connection failed ({redis_url}): {e}. "
                "System will fall back to PostgreSQL-only mode."
            )
            cls._client = None

        cls._instance = cls()
        return cls._instance

    @classmethod
    async def get_instance(cls) -> "RedisService":
        """Get or initialize Redis service instance."""
        if cls._instance is None:
            await cls.initialize()
        return cls._instance

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set a value in Redis with optional TTL.

        Args:
            key: Redis key
            value: Value to store (will be JSON serialized)
            ttl: Time to live in seconds (default: None, no expiration)

        Returns:
            True if successful, False if Redis is unavailable
        """
        if self._client is None:
            logger.debug(f"Redis unavailable, skipping set: {key}")
            return False

        try:
            # Use default TTL if not specified (1 hour for conversations)
            ttl = ttl or 3600

            # Serialize value to JSON if it's a dict/list
            if isinstance(value, (dict, list)):
                value = json.dumps(value)

            await self._client.setex(key, ttl, value)
            logger.debug(f"🔗 Redis SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Error setting Redis key {key}: {e}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from Redis.

        Args:
            key: Redis key

        Returns:
            Value if found, None otherwise
        """
        if self._client is None:
            logger.debug(f"Redis unavailable, skipping get: {key}")
            return None

        try:
            value = await self._client.get(key)
            if value is None:
                logger.debug(f"🔍 Redis MISS: {key}")
                return None

            logger.debug(f"🔍 Redis HIT: {key}")

            # Try to parse as JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Not JSON, return as-is
                return value
        except Exception as e:
            logger.error(f"Error getting Redis key {key}: {e}")
            return None

    async def delete(self, key: str) -> bool:
        """
        Delete a key from Redis.

        Args:
            key: Redis key

        Returns:
            True if key was deleted, False otherwise
        """
        if self._client is None:
            logger.debug(f"Redis unavailable, skipping delete: {key}")
            return False

        try:
            result = await self._client.delete(key)
            logger.debug(f"🗑️  Redis DELETE: {key}")
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting Redis key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis.

        Args:
            key: Redis key

        Returns:
            True if key exists, False otherwise
        """
        if self._client is None:
            return False

        try:
            result = await self._client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Error checking Redis key {key}: {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration on an existing key.

        Args:
            key: Redis key
            ttl: Time to live in seconds

        Returns:
            True if expiration was set, False otherwise
        """
        if self._client is None:
            logger.debug(f"Redis unavailable, skipping expire: {key}")
            return False

        try:
            result = await self._client.expire(key, ttl)
            logger.debug(f"⏱️  Redis EXPIRE: {key} (TTL: {ttl}s)")
            return result > 0
        except Exception as e:
            logger.error(f"Error setting expiration on Redis key {key}: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., "conversation:*")

        Returns:
            Number of keys deleted
        """
        if self._client is None:
            logger.debug(f"Redis unavailable, skipping clear_pattern: {pattern}")
            return 0

        try:
            keys = await self._client.keys(pattern)
            if not keys:
                return 0

            result = await self._client.delete(*keys)
            logger.debug(f"🗑️  Redis DELETE PATTERN: {pattern} ({result} keys)")
            return result
        except Exception as e:
            logger.error(f"Error clearing Redis pattern {pattern}: {e}")
            return 0

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client is not None:
            await self._client.close()
            logger.info("✅ Redis connection closed")

    async def health_check(self) -> bool:
        """
        Check if Redis is healthy.

        Returns:
            True if Redis is available and responding, False otherwise
        """
        if self._client is None:
            return False

        try:
            await self._client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# Conversation cache key patterns
def get_conversation_cache_key(conversation_id: str) -> str:
    """Get Redis cache key for conversation context."""
    return f"conversation:{conversation_id}:context"


def get_conversation_messages_key(conversation_id: str) -> str:
    """Get Redis cache key for conversation messages."""
    return f"conversation:{conversation_id}:messages"


def get_user_conversations_key(user_id: int) -> str:
    """Get Redis cache key for user's active conversations."""
    return f"user:{user_id}:conversations"
