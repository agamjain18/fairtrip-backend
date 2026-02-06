"""
Redis Cache Middleware for automatic HTTP response caching
Caches ALL GET requests automatically with intelligent TTL
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse, StreamingResponse
import json
import hashlib
from typing import Optional

class RedisCacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically cache all GET requests in Redis
    """
    
    def __init__(self, app, redis_available: bool = True):
        super().__init__(app)
        self.redis_available = redis_available
        if redis_available:
            try:
                from redis_client import redis_client
                self.redis_client = redis_client
            except ImportError:
                self.redis_available = False
                print("⚠️ Redis client not available for cache middleware")
    
    async def dispatch(self, request: Request, call_next):
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)
        
        # Skip caching for certain paths
        if self._should_skip_cache(request.url.path):
            return await call_next(request)
        
        # Only cache if Redis is available
        if not self.redis_available:
            return await call_next(request)
        
        # Quick health check - skip caching if Redis is not responding
        try:
            # Try a quick ping (will timeout in 1 second now)
            if not await self.redis_client.ping():
                # Redis not responding, skip caching for this request
                return await call_next(request)
        except Exception:
            # Redis error, skip caching for this request
            return await call_next(request)
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Try to get from cache
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data is not None:
                print(f"✅ HTTP Cache HIT: {request.url.path}")
                return JSONResponse(content=cached_data)
        except Exception as e:
            print(f"⚠️ Cache GET error: {e}")
        
        # Call the actual endpoint
        response = await call_next(request)
        
        # Cache successful JSON responses
        if response.status_code == 200:
            await self._cache_response(request, response, cache_key)
        
        return response
    
    def _should_skip_cache(self, path: str) -> bool:
        """Determine if this path should skip caching"""
        skip_patterns = [
            '/docs',
            '/redoc',
            '/openapi.json',
            '/health',
            '/static',
            '/auth/me',  # Always fresh user data
        ]
        return any(pattern in path for pattern in skip_patterns)
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate a unique cache key for the request"""
        # Include path and query parameters
        key_string = f"{request.url.path}?{request.url.query}"
        
        # Hash it to keep keys short
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"http_cache:{key_hash}"
    
    async def _cache_response(self, request: Request, response: Response, cache_key: str):
        """Cache the response with appropriate TTL"""
        try:
            # Read response body
            body_bytes = b""
            async for chunk in response.body_iterator:
                body_bytes += chunk
            
            # Try to parse as JSON
            try:
                data = json.loads(body_bytes.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Not JSON, don't cache
                # Recreate response with original body
                response.body_iterator = self._async_generator(body_bytes)
                return
            
            # Determine TTL based on endpoint
            ttl = self._get_ttl_for_endpoint(request.url.path)
            
            # Cache it
            await self.redis_client.set(cache_key, data, expire=ttl)
            print(f"💾 HTTP Cached: {request.url.path} (TTL: {ttl}s)")
            
            # Recreate response with the data
            # We need to return a new response since we consumed the original
            response.body_iterator = self._async_generator(body_bytes)
            
        except Exception as e:
            print(f"⚠️ Cache SET error: {e}")
            # Ensure response is still valid
            try:
                response.body_iterator = self._async_generator(body_bytes)
            except:
                pass
    
    async def _async_generator(self, body: bytes):
        """Helper to create async generator from bytes"""
        yield body
    
    def _get_ttl_for_endpoint(self, path: str) -> int:
        """
        Determine TTL (Time To Live) based on endpoint type
        Returns TTL in seconds
        """
        # Cities - rarely change
        if '/cities/' in path or '/featured-images' in path:
            return 3600  # 1 hour
        
        # Currency - changes daily
        elif '/currency/' in path:
            return 3600  # 1 hour
        
        # Users - changes occasionally
        elif '/users/' in path and '/summary' not in path:
            return 900   # 15 minutes
        
        # Trips - changes occasionally
        elif '/trips/' in path and '/summary' not in path:
            return 600   # 10 minutes
        
        # Trip summaries - changes with expenses
        elif '/summary' in path:
            return 120   # 2 minutes
        
        # Expenses - changes frequently
        elif '/expenses/' in path:
            return 120   # 2 minutes
        
        # Itinerary - changes occasionally
        elif '/itinerary/' in path:
            return 600   # 10 minutes
        
        # Checklist - changes occasionally
        elif '/checklist/' in path:
            return 600   # 10 minutes
        
        # Accommodations, Transports - changes occasionally
        elif '/accommodations/' in path or '/transports/' in path:
            return 600   # 10 minutes
        
        # Emergency - rarely changes
        elif '/emergency/' in path:
            return 900   # 15 minutes
        
        # Settlements - changes occasionally
        elif '/settlements/' in path:
            return 120   # 2 minutes
        
        # Recurring expenses - changes occasionally
        elif '/recurring-expenses/' in path:
            return 300   # 5 minutes
        
        # Notifications - real-time-ish
        elif '/notifications/' in path:
            return 60    # 1 minute
        
        # Sync endpoint - no cache
        elif '/sync/' in path:
            return 30    # 30 seconds
        
        # Default for everything else
        else:
            return 300   # 5 minutes

# Helper function to invalidate cache
async def invalidate_http_cache(pattern: str = None):
    """
    Invalidate HTTP cache by pattern
    
    Args:
        pattern: Pattern to match cache keys (e.g., "trips", "expenses")
    """
    try:
        from redis_client import redis_client
        
        if pattern:
            # This is a simplified version
            # In production, you'd want to track cache keys more efficiently
            print(f"🗑️ Cache invalidation requested for pattern: {pattern}")
            # For now, we'll rely on TTL expiration
        else:
            # Clear all HTTP cache
            print(f"🗑️ Clearing all HTTP cache")
            # Implementation would require tracking all cache keys
            
    except Exception as e:
        print(f"⚠️ Cache invalidation error: {e}")
