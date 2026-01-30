"""
Performance utilities for caching and optimization
"""
import functools
import hashlib
import json
from typing import Any, Callable
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """Redis-based cache manager"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def get(self, key: str) -> Any:
        """Get value from cache"""
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL (default 5 minutes)"""
        try:
            await self.redis.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def delete(self, key: str):
        """Delete key from cache"""
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
    
    async def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Cache clear error: {e}")


def cache_response(ttl: int = 300, key_prefix: str = ""):
    """Decorator to cache API responses"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{hashlib.md5(str(kwargs).encode()).hexdigest()}"
            
            # Try to get from cache
            # Note: You'll need to pass cache_manager as dependency
            # This is a simplified version
            
            # If not in cache, call function
            result = await func(*args, **kwargs)
            
            # Store in cache
            # await cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


async def paginate_query(collection, query: dict, page: int = 1, page_size: int = 20):
    """Paginate MongoDB query results"""
    skip = (page - 1) * page_size
    
    cursor = collection.find(query).skip(skip).limit(page_size)
    items = await cursor.to_list(length=page_size)
    
    total = await collection.count_documents(query)
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }


# Usage:
"""
from performance import CacheManager, paginate_query

# Initialize cache
cache = CacheManager(redis_client)

# Cache products list
@api_router.get("/products")
async def get_products():
    cached = await cache.get("products:all")
    if cached:
        return cached
    
    products = await get_products_from_db()
    await cache.set("products:all", products, ttl=60)
    return products

# Paginate orders
@api_router.get("/orders")
async def get_orders(page: int = 1):
    result = await paginate_query(
        db.orders,
        {"user_id": user_id},
        page=page,
        page_size=20
    )
    return result
"""
