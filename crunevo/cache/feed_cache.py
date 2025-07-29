import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from crunevo.extensions import db
from crunevo.models import FeedItem, Post, Note

logger = logging.getLogger(__name__)

# In-memory cache as fallback when Redis is unavailable
_memory_cache: Dict[int, List[Dict[str, Any]]] = {}
_cache_ttl = 300  # 5 minutes

def _get_cache_key(user_id: int, start: int, stop: int) -> str:
    """Generate cache key for feed items."""
    return f"feed:{user_id}:{start}:{stop}"

def _is_cache_valid(cached_data: List[Dict[str, Any]]) -> bool:
    """Check if cached data is still valid."""
    if not cached_data:
        return False
    
    # Check if cache is older than TTL
    for item in cached_data:
        if 'cached_at' in item:
            cached_time = datetime.fromisoformat(item['cached_at'])
            if datetime.utcnow() - cached_time > timedelta(seconds=_cache_ttl):
                return False
    return True

def cache_fetch(user_id: int, start: int, stop: int) -> List[Dict[str, Any]]:
    """Fetch feed items from cache with improved error handling."""
    try:
        # Try Redis first
        from crunevo.extensions import redis_client
        if redis_client:
            cache_key = _get_cache_key(user_id, start, stop)
            cached = redis_client.get(cache_key)
            if cached:
                data = json.loads(cached)
                if _is_cache_valid(data):
                    logger.debug(f"Cache hit for user {user_id}")
                    return data
    except Exception as e:
        logger.warning(f"Redis cache error: {e}")
    
    # Fallback to memory cache
    cache_key = _get_cache_key(user_id, start, stop)
    if cache_key in _memory_cache:
        data = _memory_cache[cache_key]
        if _is_cache_valid(data):
            logger.debug(f"Memory cache hit for user {user_id}")
            return data
    
    logger.debug(f"Cache miss for user {user_id}")
    return []

def cache_push(user_id: int, items: List[Dict[str, Any]]) -> None:
    """Push feed items to cache with improved error handling."""
    if not items:
        return
    
    # Add cache timestamp
    for item in items:
        item['cached_at'] = datetime.utcnow().isoformat()
    
    try:
        # Try Redis first
        from crunevo.extensions import redis_client
        if redis_client:
            cache_key = _get_cache_key(user_id, 0, len(items))
            redis_client.setex(
                cache_key,
                _cache_ttl,
                json.dumps(items, default=str)
            )
            logger.debug(f"Pushed {len(items)} items to Redis cache for user {user_id}")
    except Exception as e:
        logger.warning(f"Redis cache push error: {e}")
    
    # Fallback to memory cache
    cache_key = _get_cache_key(user_id, 0, len(items))
    _memory_cache[cache_key] = items
    
    # Clean old memory cache entries
    if len(_memory_cache) > 1000:
        _memory_cache.clear()
        logger.info("Cleared memory cache due to size limit")

def cache_invalidate(user_id: int) -> None:
    """Invalidate cache for a specific user."""
    try:
        from crunevo.extensions import redis_client
        if redis_client:
            # Delete all cache keys for this user
            pattern = f"feed:{user_id}:*"
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
                logger.debug(f"Invalidated {len(keys)} cache keys for user {user_id}")
    except Exception as e:
        logger.warning(f"Cache invalidation error: {e}")
    
    # Clear memory cache for this user
    keys_to_remove = [k for k in _memory_cache.keys() if f"feed:{user_id}:" in k]
    for key in keys_to_remove:
        del _memory_cache[key]
    logger.debug(f"Cleared {len(keys_to_remove)} memory cache entries for user {user_id}")

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics for monitoring."""
    try:
        from crunevo.extensions import redis_client
        redis_keys = len(redis_client.keys("feed:*")) if redis_client else 0
    except Exception:
        redis_keys = 0
    
    return {
        "memory_cache_size": len(_memory_cache),
        "redis_keys": redis_keys,
        "cache_ttl": _cache_ttl
    }
