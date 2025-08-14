"""Database Optimization Service
Advanced database query optimization, caching, and performance monitoring
"""

import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from functools import wraps
from collections import defaultdict
from datetime import datetime, timedelta
from dataclasses import dataclass
from threading import Lock
import json
import hashlib

from django.db import connection, transaction
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class QueryStats:
    """Query performance statistics"""

    query_hash: str
    execution_time: float
    rows_returned: int
    cache_hit: bool
    timestamp: datetime
    query_type: str


class QueryProfiler:
    """Query performance profiler and analyzer"""

    def __init__(self):
        self.stats: List[QueryStats] = []
        self.slow_queries: Dict[str, List[float]] = defaultdict(list)
        self.cache_stats = {"hits": 0, "misses": 0, "total_queries": 0}
        self._lock = Lock()

    def record_query(
        self,
        query_hash: str,
        execution_time: float,
        rows_returned: int,
        cache_hit: bool,
        query_type: str,
    ):
        """Record query execution statistics"""
        with self._lock:
            stat = QueryStats(
                query_hash=query_hash,
                execution_time=execution_time,
                rows_returned=rows_returned,
                cache_hit=cache_hit,
                timestamp=timezone.now(),
                query_type=query_type,
            )
            self.stats.append(stat)

            # Track slow queries (>100ms)
            if execution_time > 0.1:
                self.slow_queries[query_hash].append(execution_time)

            # Update cache stats
            self.cache_stats["total_queries"] += 1
            if cache_hit:
                self.cache_stats["hits"] += 1
            else:
                self.cache_stats["misses"] += 1

            # Keep only recent stats (last 1000 queries)
            if len(self.stats) > 1000:
                self.stats = self.stats[-1000:]

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        if not self.stats:
            return {"message": "No query statistics available"}

        recent_stats = [
            s for s in self.stats if s.timestamp > timezone.now() - timedelta(hours=1)
        ]

        avg_execution_time = sum(s.execution_time for s in recent_stats) / len(
            recent_stats
        )
        cache_hit_rate = (
            self.cache_stats["hits"] / self.cache_stats["total_queries"]
        ) * 100

        slow_query_count = len([s for s in recent_stats if s.execution_time > 0.1])

        return {
            "total_queries": len(recent_stats),
            "avg_execution_time": round(avg_execution_time * 1000, 2),  # ms
            "cache_hit_rate": round(cache_hit_rate, 2),
            "slow_queries": slow_query_count,
            "slowest_queries": self._get_slowest_queries(),
            "query_types": self._get_query_type_stats(recent_stats),
        }

    def _get_slowest_queries(self) -> List[Dict[str, Any]]:
        """Get top 5 slowest queries"""
        slow_queries = []
        for query_hash, times in self.slow_queries.items():
            if times:
                slow_queries.append(
                    {
                        "query_hash": query_hash[:16],
                        "avg_time": round(sum(times) / len(times) * 1000, 2),
                        "max_time": round(max(times) * 1000, 2),
                        "count": len(times),
                    }
                )

        return sorted(slow_queries, key=lambda x: x["avg_time"], reverse=True)[:5]

    def _get_query_type_stats(self, stats: List[QueryStats]) -> Dict[str, int]:
        """Get query type distribution"""
        type_counts = defaultdict(int)
        for stat in stats:
            type_counts[stat.query_type] += 1
        return dict(type_counts)


# Global profiler instance
query_profiler = QueryProfiler()


class AdvancedCache:
    """Advanced caching with TTL, tags, and invalidation strategies"""

    def __init__(self):
        self.default_timeout = getattr(
            settings, "CACHE_DEFAULT_TIMEOUT", 300
        )  # 5 minutes
        self.tag_prefix = "cache_tag:"
        self.dependency_map: Dict[str, set] = defaultdict(set)

    def get_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate consistent cache key"""
        key_data = f"{prefix}:{':'.join(map(str, args))}:{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str, default=None):
        """Get value from cache"""
        return cache.get(key, default)

    def set(
        self,
        key: str,
        value: Any,
        timeout: Optional[int] = None,
        tags: Optional[List[str]] = None,
    ):
        """Set value in cache with optional tags"""
        timeout = timeout or self.default_timeout
        cache.set(key, value, timeout)

        # Store tag associations
        if tags:
            for tag in tags:
                tag_key = f"{self.tag_prefix}{tag}"
                tagged_keys = cache.get(tag_key, set())
                tagged_keys.add(key)
                cache.set(tag_key, tagged_keys, timeout * 2)  # Tags live longer

    def invalidate_by_tags(self, tags: List[str]):
        """Invalidate all cache entries with given tags"""
        keys_to_delete = set()

        for tag in tags:
            tag_key = f"{self.tag_prefix}{tag}"
            tagged_keys = cache.get(tag_key, set())
            keys_to_delete.update(tagged_keys)
            cache.delete(tag_key)

        # Delete all associated keys
        for key in keys_to_delete:
            cache.delete(key)

        logger.info(f"Invalidated {len(keys_to_delete)} cache entries for tags: {tags}")

    def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        # Note: This requires Redis backend for pattern matching
        try:
            if hasattr(cache, "delete_pattern"):
                cache.delete_pattern(pattern)
            else:
                logger.warning("Pattern invalidation not supported by cache backend")
        except Exception as e:
            logger.error(f"Error invalidating cache pattern {pattern}: {e}")


# Global cache instance
advanced_cache = AdvancedCache()


def cache_query(
    timeout: int = 300, tags: Optional[List[str]] = None, key_prefix: str = "query"
):
    """Decorator for caching query results"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = advanced_cache.get_cache_key(
                key_prefix, func.__name__, *args, **kwargs
            )

            # Try to get from cache
            start_time = time.time()
            cached_result = advanced_cache.get(cache_key)

            if cached_result is not None:
                execution_time = time.time() - start_time
                query_profiler.record_query(
                    query_hash=cache_key,
                    execution_time=execution_time,
                    rows_returned=(
                        len(cached_result)
                        if isinstance(cached_result, (list, tuple))
                        else 1
                    ),
                    cache_hit=True,
                    query_type="cached",
                )
                return cached_result

            # Execute query
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Cache result
            advanced_cache.set(cache_key, result, timeout, tags)

            # Record stats
            query_profiler.record_query(
                query_hash=cache_key,
                execution_time=execution_time,
                rows_returned=len(result) if isinstance(result, (list, tuple)) else 1,
                cache_hit=False,
                query_type=func.__name__,
            )

            return result

        return wrapper

    return decorator


class DatabaseOptimizer:
    """Advanced database optimization service"""

    def __init__(self):
        self.cache = advanced_cache
        self.profiler = query_profiler

    # ===== OPTIMIZED BLOCK QUERIES =====

    @cache_query(timeout=300, tags=["blocks", "user_blocks"], key_prefix="blocks")
    def get_user_blocks_optimized(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> List[Dict]:
        """Get user blocks with optimized query and caching"""

        with connection.cursor() as cursor:
            # Raw SQL for better performance
            cursor.execute(
                """
                SELECT 
                    b.id, b.title, b.content, b.block_type, b.position,
                    b.created_at, b.updated_at, b.metadata,
                    COUNT(bt.id) as tag_count
                FROM personal_space_block b
                LEFT JOIN personal_space_block_tags bt ON b.id = bt.block_id
                WHERE b.user_id = %s AND b.is_active = true
                GROUP BY b.id, b.title, b.content, b.block_type, b.position,
                         b.created_at, b.updated_at, b.metadata
                ORDER BY b.position ASC, b.updated_at DESC
                LIMIT %s OFFSET %s
            """,
                [user_id, limit, offset],
            )

            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return results

    @cache_query(
        timeout=600, tags=["blocks", "analytics"], key_prefix="block_analytics"
    )
    def get_block_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive block analytics"""

        cutoff_date = timezone.now() - timedelta(days=days)

        with connection.cursor() as cursor:
            # Complex analytics query
            cursor.execute(
                """
                WITH block_stats AS (
                    SELECT 
                        block_type,
                        COUNT(*) as total_blocks,
                        AVG(CASE WHEN metadata->>'progress' IS NOT NULL 
                            THEN CAST(metadata->>'progress' AS INTEGER) 
                            ELSE NULL END) as avg_progress,
                        COUNT(CASE WHEN updated_at > %s THEN 1 END) as recent_updates
                    FROM personal_space_block 
                    WHERE user_id = %s AND is_active = true
                    GROUP BY block_type
                ),
                daily_activity AS (
                    SELECT 
                        DATE(updated_at) as activity_date,
                        COUNT(*) as updates_count
                    FROM personal_space_block 
                    WHERE user_id = %s AND updated_at > %s AND is_active = true
                    GROUP BY DATE(updated_at)
                    ORDER BY activity_date DESC
                    LIMIT 30
                )
                SELECT 
                    (SELECT json_agg(row_to_json(bs)) FROM block_stats bs) as block_stats,
                    (SELECT json_agg(row_to_json(da)) FROM daily_activity da) as daily_activity,
                    (SELECT COUNT(*) FROM personal_space_block WHERE user_id = %s AND is_active = true) as total_blocks,
                    (SELECT COUNT(DISTINCT block_type) FROM personal_space_block WHERE user_id = %s AND is_active = true) as unique_types
            """,
                [cutoff_date, user_id, user_id, cutoff_date, user_id, user_id],
            )

            result = cursor.fetchone()

            return {
                "block_stats": result[0] or [],
                "daily_activity": result[1] or [],
                "total_blocks": result[2] or 0,
                "unique_types": result[3] or 0,
                "period_days": days,
            }

    @cache_query(timeout=180, tags=["blocks", "search"], key_prefix="block_search")
    def search_blocks_optimized(
        self,
        user_id: int,
        query: str,
        block_types: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """Optimized full-text search for blocks"""
        with connection.cursor() as cursor:
            # Use PostgreSQL full-text search if available
            base_query = """
                SELECT 
                    b.id, b.title, b.content, b.block_type, b.position,
                    b.created_at, b.updated_at,
                    ts_rank(to_tsvector('english', COALESCE(b.title, '') || ' ' || COALESCE(b.content, '')), 
                            plainto_tsquery('english', %s)) as relevance
                FROM personal_space_block b
                WHERE b.user_id = %s 
                    AND b.is_active = true
                    AND (to_tsvector('english', COALESCE(b.title, '') || ' ' || COALESCE(b.content, '')) 
                         @@ plainto_tsquery('english', %s))
            """

            params = [query, user_id, query]

            if block_types:
                base_query += " AND b.block_type = ANY(%s)"
                params.append(block_types)

            base_query += " ORDER BY relevance DESC, b.updated_at DESC LIMIT %s"
            params.append(limit)

            try:
                cursor.execute(base_query, params)
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            except Exception as e:
                # Fallback to simple ILIKE search
                logger.warning(f"Full-text search failed, using fallback: {e}")
                fallback_query = """
                    SELECT 
                        b.id, b.title, b.content, b.block_type, b.position,
                        b.created_at, b.updated_at, 1.0 as relevance
                    FROM personal_space_block b
                    WHERE b.user_id = %s 
                        AND b.is_active = true
                        AND (b.title ILIKE %s OR b.content ILIKE %s)
                """

                fallback_params = [user_id, f"%{query}%", f"%{query}%"]

                if block_types:
                    fallback_query += " AND b.block_type = ANY(%s)"
                    fallback_params.append(block_types)

                fallback_query += " ORDER BY b.updated_at DESC LIMIT %s"
                fallback_params.append(limit)

                cursor.execute(fallback_query, fallback_params)
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return results

    # ===== BATCH OPERATIONS =====

    def bulk_update_blocks(self, user_id: int, updates: List[Dict[str, Any]]) -> bool:
        """Bulk update blocks efficiently"""
        if not updates:
            return True

        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # Prepare bulk update
                    update_cases = []
                    block_ids = []

                    for update in updates:
                        block_id = update["id"]
                        block_ids.append(block_id)

                        # Build CASE statements for each field
                        for field, value in update.items():
                            if field != "id":
                                if field == "metadata":
                                    update_cases.append(
                                        f"WHEN id = {block_id} THEN '{json.dumps(value)}'::jsonb"
                                    )
                                else:
                                    update_cases.append(f"WHEN id = {block_id} THEN %s")

                    # Execute bulk update
                    if update_cases:
                        cursor.execute(
                            f"""
                            UPDATE personal_space_block 
                            SET 
                                title = CASE {' '.join(update_cases)} ELSE title END,
                                content = CASE {' '.join(update_cases)} ELSE content END,
                                metadata = CASE {' '.join(update_cases)} ELSE metadata END,
                                updated_at = NOW()
                            WHERE id = ANY(%s) AND user_id = %s
                        """,
                            [block_ids, user_id],
                        )

                # Invalidate related caches
                self.cache.invalidate_by_tags(
                    ["blocks", "user_blocks", f"user_{user_id}"]
                )

                return True

        except Exception as e:
            logger.error(f"Bulk update failed: {e}")
            return False

    def bulk_reorder_blocks(
        self, user_id: int, block_positions: List[Tuple[int, int]]
    ) -> bool:
        """Efficiently reorder multiple blocks"""
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # Use VALUES clause for efficient bulk update
                    values_clause = ",".join(
                        [
                            f"({block_id}, {position})"
                            for block_id, position in block_positions
                        ]
                    )

                    cursor.execute(
                        f"""
                        UPDATE personal_space_block 
                        SET position = v.new_position,
                            updated_at = NOW()
                        FROM (VALUES {values_clause}) AS v(block_id, new_position)
                        WHERE personal_space_block.id = v.block_id 
                            AND personal_space_block.user_id = %s
                    """,
                        [user_id],
                    )

                # Invalidate caches
                self.cache.invalidate_by_tags(
                    ["blocks", "user_blocks", f"user_{user_id}"]
                )

                return True

        except Exception as e:
            logger.error(f"Bulk reorder failed: {e}")
            return False

    # ===== PERFORMANCE MONITORING =====

    def get_database_performance(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        with connection.cursor() as cursor:
            # Get connection stats
            cursor.execute(
                """
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity
                WHERE datname = current_database()
            """
            )

            conn_stats = cursor.fetchone()

            # Get table stats
            cursor.execute(
                """
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples
                FROM pg_stat_user_tables 
                WHERE tablename LIKE '%block%'
                ORDER BY n_live_tup DESC
            """
            )

            table_stats = cursor.fetchall()

            # Get slow queries (if pg_stat_statements is available)
            try:
                cursor.execute(
                    """
                    SELECT 
                        query,
                        calls,
                        total_time,
                        mean_time,
                        rows
                    FROM pg_stat_statements 
                    WHERE query LIKE '%personal_space_block%'
                    ORDER BY mean_time DESC 
                    LIMIT 5
                """
                )
                slow_queries = cursor.fetchall()
            except Exception:
                slow_queries = []

            return {
                "connections": {
                    "total": conn_stats[0],
                    "active": conn_stats[1],
                    "idle": conn_stats[2],
                },
                "table_stats": [
                    {
                        "schema": row[0],
                        "table": row[1],
                        "inserts": row[2],
                        "updates": row[3],
                        "deletes": row[4],
                        "live_tuples": row[5],
                        "dead_tuples": row[6],
                    }
                    for row in table_stats
                ],
                "slow_queries": [
                    {
                        "query": row[0][:100] + "..." if len(row[0]) > 100 else row[0],
                        "calls": row[1],
                        "total_time": row[2],
                        "mean_time": row[3],
                        "rows": row[4],
                    }
                    for row in slow_queries
                ],
                "query_profiler": self.profiler.get_performance_report(),
            }

    # ===== CACHE MANAGEMENT =====

    def warm_cache(self, user_id: int):
        """Pre-warm cache with frequently accessed data"""
        try:
            # Pre-load user blocks
            self.get_user_blocks_optimized(user_id, limit=20)

            # Pre-load analytics
            self.get_block_analytics(user_id, days=7)

            logger.info(f"Cache warmed for user {user_id}")

        except Exception as e:
            logger.error(f"Cache warming failed for user {user_id}: {e}")

    def clear_user_cache(self, user_id: int):
        """Clear all cache entries for a specific user"""
        self.cache.invalidate_by_tags([f"user_{user_id}", "user_blocks"])
        logger.info(f"Cache cleared for user {user_id}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        return {
            "profiler_stats": self.profiler.cache_stats,
            "cache_info": {
                "backend": str(cache.__class__),
                "default_timeout": self.cache.default_timeout,
            },
        }

    # ===== MAINTENANCE =====

    def analyze_tables(self):
        """Run ANALYZE on block tables for better query planning"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("ANALYZE personal_space_block")
                cursor.execute("ANALYZE personal_space_block_tags")

            logger.info("Table analysis completed")

        except Exception as e:
            logger.error(f"Table analysis failed: {e}")

    def cleanup_old_stats(self, days: int = 7):
        """Clean up old performance statistics"""
        cutoff_date = timezone.now() - timedelta(days=days)
        self.profiler.stats = [
            stat for stat in self.profiler.stats if stat.timestamp > cutoff_date
        ]

        logger.info(f"Cleaned up stats older than {days} days")


# Global optimizer instance
database_optimizer = DatabaseOptimizer()


# Utility functions for easy access
def get_optimized_blocks(user_id: int, **kwargs):
    """Get user blocks with optimization"""
    return database_optimizer.get_user_blocks_optimized(user_id, **kwargs)


def search_blocks(user_id: int, query: str, **kwargs):
    """Search blocks with optimization"""
    return database_optimizer.search_blocks_optimized(user_id, query, **kwargs)


def get_block_analytics(user_id: int, **kwargs):
    """Get block analytics with caching"""
    return database_optimizer.get_block_analytics(user_id, **kwargs)


def bulk_update_blocks(user_id: int, updates: List[Dict]):
    """Bulk update blocks efficiently"""
    return database_optimizer.bulk_update_blocks(user_id, updates)


def get_performance_report():
    """Get comprehensive performance report"""
    return database_optimizer.get_database_performance()
