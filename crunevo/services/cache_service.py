from typing import Any, Optional, Dict, List
from functools import wraps
from datetime import datetime, timedelta
import json
import hashlib
from flask import current_app
from crunevo.extensions import redis_client


class CacheService:
    """Service for caching data to improve performance."""
    
    # Cache key prefixes
    USER_BLOCKS_PREFIX = 'user_blocks'
    USER_TEMPLATES_PREFIX = 'user_templates'
    ANALYTICS_PREFIX = 'analytics'
    DASHBOARD_PREFIX = 'dashboard'
    BLOCK_ANALYTICS_PREFIX = 'block_analytics'
    
    # Default cache durations (in seconds)
    DEFAULT_TTL = 300  # 5 minutes
    ANALYTICS_TTL = 600  # 10 minutes
    DASHBOARD_TTL = 180  # 3 minutes
    TEMPLATES_TTL = 900  # 15 minutes
    
    @staticmethod
    def _get_cache_key(prefix: str, *args) -> str:
        """Generate a cache key from prefix and arguments."""
        key_parts = [prefix] + [str(arg) for arg in args]
        return ':'.join(key_parts)
    
    @staticmethod
    def _serialize_data(data: Any) -> str:
        """Serialize data for caching."""
        try:
            return json.dumps(data, default=str, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(data)
    
    @staticmethod
    def _deserialize_data(data: str) -> Any:
        """Deserialize cached data."""
        try:
            return json.loads(data)
        except (TypeError, ValueError, json.JSONDecodeError):
            return data
    
    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get data from cache."""
        try:
            if not redis_client:
                return None
            
            cached_data = redis_client.get(key)
            if cached_data:
                return CacheService._deserialize_data(cached_data)
            return None
        except Exception as e:
            current_app.logger.warning(f"Cache get error: {e}")
            return None
    
    @staticmethod
    def set(key: str, data: Any, ttl: int = DEFAULT_TTL) -> bool:
        """Set data in cache with TTL."""
        try:
            if not redis_client:
                return False
            
            serialized_data = CacheService._serialize_data(data)
            return redis_client.setex(key, ttl, serialized_data)
        except Exception as e:
            current_app.logger.warning(f"Cache set error: {e}")
            return False
    
    @staticmethod
    def delete(key: str) -> bool:
        """Delete data from cache."""
        try:
            if not redis_client:
                return False
            
            return bool(redis_client.delete(key))
        except Exception as e:
            current_app.logger.warning(f"Cache delete error: {e}")
            return False
    
    @staticmethod
    def delete_pattern(pattern: str) -> int:
        """Delete all keys matching a pattern."""
        try:
            if not redis_client:
                return 0
            
            keys = redis_client.keys(pattern)
            if keys:
                return redis_client.delete(*keys)
            return 0
        except Exception as e:
            current_app.logger.warning(f"Cache delete pattern error: {e}")
            return 0
    
    @staticmethod
    def invalidate_user_cache(user_id: int) -> None:
        """Invalidate all cache entries for a user."""
        patterns = [
            f"{CacheService.USER_BLOCKS_PREFIX}:{user_id}:*",
            f"{CacheService.USER_TEMPLATES_PREFIX}:{user_id}:*",
            f"{CacheService.ANALYTICS_PREFIX}:{user_id}:*",
            f"{CacheService.DASHBOARD_PREFIX}:{user_id}:*",
            f"{CacheService.BLOCK_ANALYTICS_PREFIX}:{user_id}:*"
        ]
        
        for pattern in patterns:
            CacheService.delete_pattern(pattern)
    
    @staticmethod
    def get_user_blocks_cache_key(user_id: int, block_type: Optional[str] = None, 
                                 status: str = 'active') -> str:
        """Get cache key for user blocks."""
        key_parts = [CacheService.USER_BLOCKS_PREFIX, str(user_id), status]
        if block_type:
            key_parts.append(block_type)
        return ':'.join(key_parts)
    
    @staticmethod
    def get_user_templates_cache_key(user_id: int, category: Optional[str] = None, 
                                   include_public: bool = True) -> str:
        """Get cache key for user templates."""
        key_parts = [CacheService.USER_TEMPLATES_PREFIX, str(user_id), str(include_public)]
        if category:
            key_parts.append(category)
        return ':'.join(key_parts)
    
    @staticmethod
    def get_analytics_cache_key(user_id: int, analytics_type: str) -> str:
        """Get cache key for analytics data."""
        return CacheService._get_cache_key(
            CacheService.ANALYTICS_PREFIX, user_id, analytics_type
        )
    
    @staticmethod
    def get_dashboard_cache_key(user_id: int) -> str:
        """Get cache key for dashboard data."""
        return CacheService._get_cache_key(
            CacheService.DASHBOARD_PREFIX, user_id
        )
    
    @staticmethod
    def get_block_analytics_cache_key(user_id: int) -> str:
        """Get cache key for block analytics."""
        return CacheService._get_cache_key(
            CacheService.BLOCK_ANALYTICS_PREFIX, user_id
        )


def cached(ttl: int = CacheService.DEFAULT_TTL, key_func: Optional[callable] = None):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend([str(arg) for arg in args])
                key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
                cache_key = hashlib.md5(':'.join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            cached_result = CacheService.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            CacheService.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


def cache_user_blocks(user_id: int, block_type: Optional[str] = None, status: str = 'active'):
    """Cache key function for user blocks."""
    def key_func(*args, **kwargs):
        return CacheService.get_user_blocks_cache_key(user_id, block_type, status)
    return key_func


def cache_user_templates(user_id: int, category: Optional[str] = None, include_public: bool = True):
    """Cache key function for user templates."""
    def key_func(*args, **kwargs):
        return CacheService.get_user_templates_cache_key(user_id, category, include_public)
    return key_func


def cache_analytics(user_id: int, analytics_type: str):
    """Cache key function for analytics."""
    def key_func(*args, **kwargs):
        return CacheService.get_analytics_cache_key(user_id, analytics_type)
    return key_func


def cache_dashboard(user_id: int):
    """Cache key function for dashboard."""
    def key_func(*args, **kwargs):
        return CacheService.get_dashboard_cache_key(user_id)
    return key_func


def cache_block_analytics(user_id: int):
    """Cache key function for block analytics."""
    def key_func(*args, **kwargs):
        return CacheService.get_block_analytics_cache_key(user_id)
    return key_func


class CacheInvalidator:
    """Helper class for cache invalidation strategies."""
    
    @staticmethod
    def on_block_change(user_id: int) -> None:
        """Invalidate caches when blocks change."""
        # Invalidate user blocks cache
        CacheService.delete_pattern(f"{CacheService.USER_BLOCKS_PREFIX}:{user_id}:*")
        
        # Invalidate analytics cache
        CacheService.delete_pattern(f"{CacheService.ANALYTICS_PREFIX}:{user_id}:*")
        CacheService.delete_pattern(f"{CacheService.DASHBOARD_PREFIX}:{user_id}:*")
        CacheService.delete_pattern(f"{CacheService.BLOCK_ANALYTICS_PREFIX}:{user_id}:*")
    
    @staticmethod
    def on_template_change(user_id: int) -> None:
        """Invalidate caches when templates change."""
        # Invalidate user templates cache
        CacheService.delete_pattern(f"{CacheService.USER_TEMPLATES_PREFIX}:{user_id}:*")
        
        # Also invalidate public templates cache for all users
        CacheService.delete_pattern(f"{CacheService.USER_TEMPLATES_PREFIX}:*:True*")
    
    @staticmethod
    def on_user_activity(user_id: int) -> None:
        """Invalidate analytics caches on user activity."""
        CacheService.delete_pattern(f"{CacheService.ANALYTICS_PREFIX}:{user_id}:*")
        CacheService.delete_pattern(f"{CacheService.DASHBOARD_PREFIX}:{user_id}:*")


# Utility functions for common caching patterns
def get_or_set_cache(key: str, fetch_func: callable, ttl: int = CacheService.DEFAULT_TTL) -> Any:
    """Get data from cache or fetch and cache it."""
    cached_data = CacheService.get(key)
    if cached_data is not None:
        return cached_data
    
    # Fetch fresh data
    fresh_data = fetch_func()
    CacheService.set(key, fresh_data, ttl)
    return fresh_data


def warm_user_cache(user_id: int) -> None:
    """Pre-warm cache for a user with commonly accessed data."""
    from crunevo.services.block_service import BlockService
    from crunevo.services.analytics_service import AnalyticsService
    from crunevo.services.template_service import TemplateService
    
    try:
        # Warm blocks cache
        blocks_key = CacheService.get_user_blocks_cache_key(user_id)
        if not CacheService.get(blocks_key):
            blocks = BlockService.get_user_blocks(user_id)
            CacheService.set(blocks_key, [b.to_dict() for b in blocks], CacheService.DEFAULT_TTL)
        
        # Warm dashboard cache
        dashboard_key = CacheService.get_dashboard_cache_key(user_id)
        if not CacheService.get(dashboard_key):
            dashboard_data = AnalyticsService.get_dashboard_metrics(user_id)
            CacheService.set(dashboard_key, dashboard_data, CacheService.DASHBOARD_TTL)
        
        # Warm templates cache
        templates_key = CacheService.get_user_templates_cache_key(user_id)
        if not CacheService.get(templates_key):
            templates = TemplateService.get_templates(user_id)
            CacheService.set(templates_key, [t.to_dict() for t in templates], CacheService.TEMPLATES_TTL)
    
    except Exception as e:
        current_app.logger.warning(f"Cache warming error for user {user_id}: {e}")