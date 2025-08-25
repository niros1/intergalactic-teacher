"""Redis client configuration and utilities."""

import json
import logging
from typing import Any, Optional, Union

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper with utilities."""
    
    def __init__(self):
        self._client: Optional[Redis] = None
    
    @property
    def client(self) -> Redis:
        """Get Redis client instance."""
        if self._client is None:
            self._client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
        return self._client
    
    async def ping(self) -> bool:
        """Check if Redis is available."""
        try:
            await self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
        json_serialize: bool = True
    ) -> bool:
        """Set a key-value pair in Redis."""
        try:
            if json_serialize:
                value = json.dumps(value)
            
            result = await self.client.set(key, value, ex=expire)
            return result is True
            
        except Exception as e:
            logger.error(f"Redis SET failed for key {key}: {e}")
            return False
    
    async def get(
        self,
        key: str,
        json_deserialize: bool = True,
        default: Any = None
    ) -> Any:
        """Get a value from Redis."""
        try:
            value = await self.client.get(key)
            
            if value is None:
                return default
            
            if json_deserialize:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            
            return value
            
        except Exception as e:
            logger.error(f"Redis GET failed for key {key}: {e}")
            return default
    
    async def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        try:
            result = await self.client.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis DELETE failed for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        try:
            result = await self.client.exists(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis EXISTS failed for key {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for a key."""
        try:
            result = await self.client.expire(key, seconds)
            return result is True
            
        except Exception as e:
            logger.error(f"Redis EXPIRE failed for key {key}: {e}")
            return False
    
    async def hset(
        self,
        key: str,
        field: str,
        value: Any,
        json_serialize: bool = True
    ) -> bool:
        """Set a hash field."""
        try:
            if json_serialize:
                value = json.dumps(value)
            
            result = await self.client.hset(key, field, value)
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis HSET failed for key {key}, field {field}: {e}")
            return False
    
    async def hget(
        self,
        key: str,
        field: str,
        json_deserialize: bool = True,
        default: Any = None
    ) -> Any:
        """Get a hash field value."""
        try:
            value = await self.client.hget(key, field)
            
            if value is None:
                return default
            
            if json_deserialize:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            
            return value
            
        except Exception as e:
            logger.error(f"Redis HGET failed for key {key}, field {field}: {e}")
            return default
    
    async def hgetall(
        self,
        key: str,
        json_deserialize: bool = True
    ) -> dict:
        """Get all hash fields and values."""
        try:
            data = await self.client.hgetall(key)
            
            if not data:
                return {}
            
            if json_deserialize:
                result = {}
                for field, value in data.items():
                    try:
                        result[field] = json.loads(value)
                    except json.JSONDecodeError:
                        result[field] = value
                return result
            
            return data
            
        except Exception as e:
            logger.error(f"Redis HGETALL failed for key {key}: {e}")
            return {}
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment a counter."""
        try:
            result = await self.client.incrby(key, amount)
            return result
            
        except Exception as e:
            logger.error(f"Redis INCR failed for key {key}: {e}")
            return 0
    
    async def sadd(self, key: str, *values: Any) -> int:
        """Add values to a set."""
        try:
            # Convert values to strings
            str_values = [json.dumps(v) if not isinstance(v, str) else v for v in values]
            result = await self.client.sadd(key, *str_values)
            return result
            
        except Exception as e:
            logger.error(f"Redis SADD failed for key {key}: {e}")
            return 0
    
    async def smembers(self, key: str, json_deserialize: bool = True) -> set:
        """Get all members of a set."""
        try:
            members = await self.client.smembers(key)
            
            if json_deserialize:
                result = set()
                for member in members:
                    try:
                        result.add(json.loads(member))
                    except json.JSONDecodeError:
                        result.add(member)
                return result
            
            return members
            
        except Exception as e:
            logger.error(f"Redis SMEMBERS failed for key {key}: {e}")
            return set()
    
    async def cache_user_session(
        self,
        user_id: int,
        session_data: dict,
        expire: int = 3600
    ) -> bool:
        """Cache user session data."""
        key = f"user_session:{user_id}"
        return await self.set(key, session_data, expire=expire)
    
    async def get_user_session(self, user_id: int) -> Optional[dict]:
        """Get cached user session data."""
        key = f"user_session:{user_id}"
        return await self.get(key)
    
    async def invalidate_user_session(self, user_id: int) -> bool:
        """Invalidate user session cache."""
        key = f"user_session:{user_id}"
        return await self.delete(key)
    
    async def cache_story_content(
        self,
        story_id: int,
        content: dict,
        expire: int = 1800  # 30 minutes
    ) -> bool:
        """Cache generated story content."""
        key = f"story_content:{story_id}"
        return await self.set(key, content, expire=expire)
    
    async def get_cached_story_content(self, story_id: int) -> Optional[dict]:
        """Get cached story content."""
        key = f"story_content:{story_id}"
        return await self.get(key)
    
    async def rate_limit_check(
        self,
        identifier: str,
        limit: int = 100,
        window: int = 60
    ) -> tuple[bool, int]:
        """Check and update rate limit for an identifier."""
        key = f"rate_limit:{identifier}"
        
        try:
            current = await self.incr(key)
            
            if current == 1:
                # First request in the window, set expiration
                await self.expire(key, window)
            
            remaining = max(0, limit - current)
            is_allowed = current <= limit
            
            return is_allowed, remaining
            
        except Exception as e:
            logger.error(f"Rate limit check failed for {identifier}: {e}")
            # Allow request if rate limiting fails
            return True, limit


# Create global Redis client instance
redis_client = RedisClient()