"""
Redis Client for New Folder Backend
Provides async Redis operations with automatic key prefixing
"""

import redis.asyncio as aioredis
from redis.asyncio import Redis
from typing import Optional, Any
import json
import os
from dotenv import load_dotenv

load_dotenv()


class RedisClient:
    """Async Redis client with key prefixing and JSON serialization"""
    
    def __init__(self):
        self.host = os.getenv('REDIS_HOST', 'localhost')
        self.port = int(os.getenv('REDIS_PORT', 6379))
        self.password = os.getenv('REDIS_PASSWORD', None)
        self.db = int(os.getenv('REDIS_DB', 2))  # Database 2 for New Folder
        self.prefix = os.getenv('REDIS_PREFIX', 'new_folder')
        self.client: Optional[Redis] = None
    
    async def connect(self) -> Redis:
        """Initialize Redis connection"""
        if self.client is None:
            # Build Redis URL based on whether password is set
            if self.password:
                redis_url = f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
            else:
                redis_url = f"redis://{self.host}:{self.port}/{self.db}"
            
            self.client = await aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=1,  # Reduced from 5 to 1 second
                socket_timeout=1,          # Reduced from 5 to 1 second
                max_connections=50
            )
        return self.client
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            self.client = None
    
    def _get_key(self, key: str) -> str:
        """Add prefix to key"""
        return f"{self.prefix}:{key}"
    
    async def ping(self) -> bool:
        """Test Redis connection"""
        try:
            return await self.client.ping()
        except Exception:
            return False
    
    # ==================== String Operations ====================
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[int] = None
    ) -> bool:
        """Set a key-value pair with optional expiration"""
        key = self._get_key(key)
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return await self.client.set(key, value, ex=expire)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key with automatic JSON parsing"""
        key = self._get_key(key)
        value = await self.client.get(key)
        if value:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return None
    
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys"""
        prefixed_keys = [self._get_key(key) for key in keys]
        return await self.client.delete(*prefixed_keys)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        key = self._get_key(key)
        return await self.client.exists(key) > 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for a key"""
        key = self._get_key(key)
        return await self.client.expire(key, seconds)
    
    async def ttl(self, key: str) -> int:
        """Get time to live for a key"""
        key = self._get_key(key)
        return await self.client.ttl(key)
    
    # ==================== Hash Operations ====================
    
    async def hset(self, name: str, key: str, value: Any) -> int:
        """Set hash field"""
        name = self._get_key(name)
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return await self.client.hset(name, key, value)
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """Get hash field"""
        name = self._get_key(name)
        value = await self.client.hget(name, key)
        if value:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return None
    
    async def hgetall(self, name: str) -> dict:
        """Get all hash fields"""
        name = self._get_key(name)
        data = await self.client.hgetall(name)
        result = {}
        for k, v in data.items():
            try:
                result[k] = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                result[k] = v
        return result
    
    async def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields"""
        name = self._get_key(name)
        return await self.client.hdel(name, *keys)
    
    # ==================== List Operations ====================
    
    async def lpush(self, key: str, *values: Any) -> int:
        """Push values to the left of list"""
        key = self._get_key(key)
        serialized = [json.dumps(v) if isinstance(v, (dict, list)) else v for v in values]
        return await self.client.lpush(key, *serialized)
    
    async def rpush(self, key: str, *values: Any) -> int:
        """Push values to the right of list"""
        key = self._get_key(key)
        serialized = [json.dumps(v) if isinstance(v, (dict, list)) else v for v in values]
        return await self.client.rpush(key, *serialized)
    
    async def lrange(self, key: str, start: int = 0, end: int = -1) -> list:
        """Get range of values from list"""
        key = self._get_key(key)
        values = await self.client.lrange(key, start, end)
        result = []
        for v in values:
            try:
                result.append(json.loads(v))
            except (json.JSONDecodeError, TypeError):
                result.append(v)
        return result
    
    async def llen(self, key: str) -> int:
        """Get length of list"""
        key = self._get_key(key)
        return await self.client.llen(key)
    
    # ==================== Set Operations ====================
    
    async def sadd(self, key: str, *values: Any) -> int:
        """Add members to set"""
        key = self._get_key(key)
        serialized = [json.dumps(v) if isinstance(v, (dict, list)) else v for v in values]
        return await self.client.sadd(key, *serialized)
    
    async def smembers(self, key: str) -> set:
        """Get all members of set"""
        key = self._get_key(key)
        values = await self.client.smembers(key)
        result = set()
        for v in values:
            try:
                result.add(json.loads(v))
            except (json.JSONDecodeError, TypeError):
                result.add(v)
        return result
    
    async def srem(self, key: str, *values: Any) -> int:
        """Remove members from set"""
        key = self._get_key(key)
        serialized = [json.dumps(v) if isinstance(v, (dict, list)) else v for v in values]
        return await self.client.srem(key, *serialized)
    
    # ==================== Utility Operations ====================
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        key = self._get_key(key)
        return await self.client.incrby(key, amount)
    
    async def decr(self, key: str, amount: int = 1) -> int:
        """Decrement counter"""
        key = self._get_key(key)
        return await self.client.decrby(key, amount)
    
    async def keys(self, pattern: str = "*") -> list:
        """Get keys matching pattern"""
        pattern = self._get_key(pattern)
        return await self.client.keys(pattern)


# Global Redis client instance
redis_client = RedisClient()
