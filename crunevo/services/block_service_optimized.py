from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy import and_, text
from crunevo.extensions import db
from crunevo.models import PersonalSpaceBlock
import logging
from functools import wraps


class CacheManager:
    """Simple in-memory cache for block operations."""

    def __init__(self):
        self._cache = {}
        self._ttl = {}
        self.default_ttl = 300  # 5 minutes

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            if self._ttl.get(key, 0) > datetime.utcnow().timestamp():
                return self._cache[key]
            else:
                self.delete(key)
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self._cache[key] = value
        self._ttl[key] = datetime.utcnow().timestamp() + (ttl or self.default_ttl)

    def delete(self, key: str) -> None:
        self._cache.pop(key, None)
        self._ttl.pop(key, None)

    def clear_user_cache(self, user_id: int) -> None:
        """Clear all cache entries for a specific user."""
        keys_to_delete = [k for k in self._cache.keys() if f"user_{user_id}" in k]
        for key in keys_to_delete:
            self.delete(key)


# Global cache instance
cache = CacheManager()


def with_cache(cache_key_func, ttl=300):
    """Decorator for caching function results."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = cache_key_func(*args, **kwargs)

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        return wrapper

    return decorator


def invalidate_user_cache(user_id: int):
    """Invalidate all cache entries for a user."""
    cache.clear_user_cache(user_id)


class OptimizedBlockService:
    """Optimized service for managing personal space blocks with enhanced performance."""

    # Block type configurations
    BLOCK_TYPE_CONFIGS = {
        "tarea": {
            "defaults": {"completed": False, "priority": "medium", "due_date": None},
            "required_fields": ["title"],
            "max_content_length": 5000,
        },
        "objetivo": {
            "defaults": {"progress": 0, "target_date": None, "status": "no_iniciada"},
            "required_fields": ["title"],
            "max_content_length": 10000,
        },
        "nota": {
            "defaults": {},
            "required_fields": ["title"],
            "max_content_length": 50000,
        },
        "lista": {
            "defaults": {"tasks": []},
            "required_fields": ["title"],
            "max_content_length": 10000,
        },
        "kanban": {
            "defaults": {"columns": {"por_hacer": [], "en_progreso": [], "hecho": []}},
            "required_fields": ["title"],
            "max_content_length": 20000,
        },
        "recordatorio": {
            "defaults": {"due_date": None, "priority": "medium"},
            "required_fields": ["title", "due_date"],
            "max_content_length": 2000,
        },
    }

    @staticmethod
    def create_block(user_id: int, block_data: Dict[str, Any]) -> PersonalSpaceBlock:
        """Create a new block with optimized validation and defaults."""
        try:
            # Enhanced validation
            validation_result = OptimizedBlockService._validate_block_data(block_data)
            if not validation_result["valid"]:
                raise ValueError(
                    f"Validation errors: {', '.join(validation_result['errors'])}"
                )

            cleaned_data = validation_result["cleaned_data"]

            # Optimized order index calculation using raw SQL for better performance
            max_order_result = db.session.execute(
                text(
                    "SELECT COALESCE(MAX(order_index), 0) FROM personal_space_blocks WHERE user_id = :user_id"
                ),
                {"user_id": user_id},
            ).scalar()

            # Create block with optimized defaults
            block = PersonalSpaceBlock(
                user_id=user_id,
                type=cleaned_data["type"],
                title=cleaned_data.get("title", f"Nuevo {cleaned_data['type']}"),
                content=cleaned_data.get("content", ""),
                metadata_json=OptimizedBlockService._get_enhanced_metadata(
                    cleaned_data
                ),
                order_index=(max_order_result or 0) + 1,
                status="active",
            )

            db.session.add(block)
            db.session.commit()

            # Invalidate cache
            invalidate_user_cache(user_id)

            # Log creation for analytics
            OptimizedBlockService._log_block_action(
                "create", user_id, block.id, block.type
            )

            return block

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating block for user {user_id}: {str(e)}")
            raise

    @staticmethod
    def _validate_block_data(block_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced validation with type-specific rules."""
        errors = []
        cleaned_data = {}

        # Type validation
        block_type = block_data.get("type", "").strip()
        if not block_type or block_type not in OptimizedBlockService.BLOCK_TYPE_CONFIGS:
            errors.append(f"Invalid block type: {block_type}")
            return {"valid": False, "errors": errors, "cleaned_data": {}}

        cleaned_data["type"] = block_type
        config = OptimizedBlockService.BLOCK_TYPE_CONFIGS[block_type]

        # Title validation
        title = block_data.get("title", "").strip()
        if not title and "title" in config["required_fields"]:
            errors.append("Title is required")
        elif len(title) > 255:
            errors.append("Title cannot exceed 255 characters")
        else:
            cleaned_data["title"] = title

        # Content validation
        content = block_data.get("content", "").strip()
        if len(content) > config["max_content_length"]:
            errors.append(
                f"Content cannot exceed {config['max_content_length']} characters"
            )
        else:
            cleaned_data["content"] = content

        # Metadata validation
        metadata = block_data.get("metadata", {})
        if isinstance(metadata, dict):
            cleaned_data["metadata"] = OptimizedBlockService._validate_metadata(
                metadata, block_type
            )
        else:
            errors.append("Metadata must be a valid object")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "cleaned_data": cleaned_data,
        }

    @staticmethod
    def _validate_metadata(metadata: Dict[str, Any], block_type: str) -> Dict[str, Any]:
        """Validate and clean metadata based on block type."""
        config = OptimizedBlockService.BLOCK_TYPE_CONFIGS[block_type]
        cleaned_metadata = config["defaults"].copy()

        # Type-specific metadata validation
        if block_type == "tarea":
            if "completed" in metadata:
                cleaned_metadata["completed"] = bool(metadata["completed"])
            if "priority" in metadata and metadata["priority"] in [
                "low",
                "medium",
                "high",
                "urgent",
            ]:
                cleaned_metadata["priority"] = metadata["priority"]
            if "due_date" in metadata:
                cleaned_metadata["due_date"] = metadata["due_date"]

        elif block_type == "objetivo":
            if "progress" in metadata:
                progress = max(0, min(100, int(metadata.get("progress", 0))))
                cleaned_metadata["progress"] = progress
            if "status" in metadata and metadata["status"] in [
                "no_iniciada",
                "en_progreso",
                "cumplida",
            ]:
                cleaned_metadata["status"] = metadata["status"]
            if "target_date" in metadata:
                cleaned_metadata["target_date"] = metadata["target_date"]

        elif block_type == "lista":
            if "tasks" in metadata and isinstance(metadata["tasks"], list):
                cleaned_metadata["tasks"] = metadata["tasks"][:50]  # Limit to 50 tasks

        elif block_type == "kanban":
            if "columns" in metadata and isinstance(metadata["columns"], dict):
                cleaned_metadata["columns"] = metadata["columns"]

        # Common metadata fields
        for field in ["color", "icon", "tags"]:
            if field in metadata:
                cleaned_metadata[field] = metadata[field]

        return cleaned_metadata

    @staticmethod
    def _get_enhanced_metadata(cleaned_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get enhanced metadata with defaults and computed fields."""
        block_type = cleaned_data["type"]
        metadata = cleaned_data.get("metadata", {})

        # Add creation timestamp
        metadata["created_at"] = datetime.utcnow().isoformat()

        # Add computed fields
        if block_type == "tarea":
            metadata["estimated_duration"] = metadata.get(
                "estimated_duration", 60
            )  # minutes
        elif block_type == "objetivo":
            metadata["difficulty"] = metadata.get("difficulty", "medium")

        return metadata

    @staticmethod
    @with_cache(
        lambda user_id, **kwargs: f"user_{user_id}_blocks_{kwargs.get('status', 'active')}_{kwargs.get('block_type', 'all')}"
    )
    def get_user_blocks(
        user_id: int,
        status: str = "active",
        block_type: Optional[str] = None,
        include_metadata: bool = True,
    ) -> List[Dict[str, Any]]:
        """Get user blocks with optimized querying and caching."""
        try:
            # Build optimized query
            query = db.session.query(PersonalSpaceBlock).filter_by(
                user_id=user_id, status=status
            )

            if block_type:
                query = query.filter_by(type=block_type)

            # Use index-optimized ordering
            blocks = query.order_by(PersonalSpaceBlock.order_index.asc()).all()

            # Convert to dictionaries for better serialization
            result = []
            for block in blocks:
                block_dict = {
                    "id": block.id,
                    "type": block.type,
                    "title": block.title,
                    "content": block.content,
                    "order_index": block.order_index,
                    "status": block.status,
                    "created_at": block.created_at.isoformat(),
                    "updated_at": block.updated_at.isoformat(),
                }

                if include_metadata:
                    block_dict["metadata"] = block.metadata_json or {}

                result.append(block_dict)

            return result

        except Exception as e:
            logging.error(f"Error fetching blocks for user {user_id}: {str(e)}")
            return []

    @staticmethod
    def update_block(
        block_id: str, user_id: int, update_data: Dict[str, Any]
    ) -> Optional[PersonalSpaceBlock]:
        """Update a block with optimized validation and caching."""
        try:
            # Use optimized query with explicit user filter for security
            block = (
                db.session.query(PersonalSpaceBlock)
                .filter(
                    and_(
                        PersonalSpaceBlock.id == block_id,
                        PersonalSpaceBlock.user_id == user_id,
                        PersonalSpaceBlock.status != "deleted",
                    )
                )
                .first()
            )

            if not block:
                return None

            # Prepare validation data
            current_data = {
                "type": block.type,
                "title": update_data.get("title", block.title),
                "content": update_data.get("content", block.content),
                "metadata": update_data.get("metadata", block.metadata_json or {}),
            }

            # Validate update
            validation_result = OptimizedBlockService._validate_block_data(current_data)
            if not validation_result["valid"]:
                raise ValueError(
                    f"Validation errors: {', '.join(validation_result['errors'])}"
                )

            cleaned_data = validation_result["cleaned_data"]

            # Apply updates efficiently
            update_fields = {}
            for field in ["title", "content", "status"]:
                if field in update_data and field in cleaned_data:
                    update_fields[field] = cleaned_data[field]

            if "metadata" in update_data:
                update_fields["metadata_json"] = cleaned_data["metadata"]

            if update_fields:
                update_fields["updated_at"] = datetime.utcnow()

                # Use bulk update for better performance
                db.session.query(PersonalSpaceBlock).filter_by(id=block_id).update(
                    update_fields
                )
                db.session.commit()

                # Refresh the object
                db.session.refresh(block)

            # Invalidate cache
            invalidate_user_cache(user_id)

            # Log update for analytics
            OptimizedBlockService._log_block_action(
                "update", user_id, block.id, block.type
            )

            return block

        except Exception as e:
            db.session.rollback()
            logging.error(
                f"Error updating block {block_id} for user {user_id}: {str(e)}"
            )
            raise

    @staticmethod
    def bulk_update_blocks(
        user_id: int, updates: List[Dict[str, Any]]
    ) -> Tuple[int, List[str]]:
        """Bulk update multiple blocks for better performance."""
        updated_count = 0
        errors = []

        try:
            for update in updates:
                block_id = update.get("id")
                if not block_id:
                    errors.append("Missing block ID")
                    continue

                try:
                    result = OptimizedBlockService.update_block(
                        block_id, user_id, update
                    )
                    if result:
                        updated_count += 1
                    else:
                        errors.append(f"Block {block_id} not found")
                except Exception as e:
                    errors.append(f"Error updating block {block_id}: {str(e)}")

            return updated_count, errors

        except Exception as e:
            logging.error(f"Error in bulk update for user {user_id}: {str(e)}")
            return updated_count, errors

    @staticmethod
    def get_block_analytics(user_id: int) -> Dict[str, Any]:
        """Get comprehensive block analytics with optimized queries."""
        try:
            # Use raw SQL for better performance on analytics
            analytics_query = text(
                """
                SELECT 
                    type,
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    AVG(CASE WHEN metadata_json->>'progress' IS NOT NULL 
                        THEN CAST(metadata_json->>'progress' AS INTEGER) END) as avg_progress
                FROM personal_space_blocks 
                WHERE user_id = :user_id 
                GROUP BY type
            """
            )

            result = db.session.execute(analytics_query, {"user_id": user_id})

            analytics = {
                "by_type": {},
                "total_blocks": 0,
                "active_blocks": 0,
                "completion_rate": 0,
            }

            total_active = 0
            total_completed = 0

            for row in result:
                analytics["by_type"][row.type] = {
                    "total": row.total,
                    "active": row.active,
                    "completed": row.completed,
                    "avg_progress": round(row.avg_progress or 0, 1),
                }
                analytics["total_blocks"] += row.total
                total_active += row.active
                total_completed += row.completed

            analytics["active_blocks"] = total_active
            analytics["completion_rate"] = round(
                (total_completed / total_active * 100) if total_active > 0 else 0, 1
            )

            return analytics

        except Exception as e:
            logging.error(f"Error getting analytics for user {user_id}: {str(e)}")
            return {"error": "Failed to load analytics"}

    @staticmethod
    def _log_block_action(
        action: str, user_id: int, block_id: str, block_type: str
    ) -> None:
        """Log block actions for analytics (async in production)."""
        try:
            # In production, this would be sent to an analytics service
            logging.info(
                f"Block action: {action} - User: {user_id} - Block: {block_id} - Type: {block_type}"
            )
        except Exception:
            pass  # Don't fail the main operation if logging fails

    @staticmethod
    def cleanup_deleted_blocks(days_old: int = 30) -> int:
        """Clean up blocks that have been deleted for more than specified days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)

            deleted_count = (
                db.session.query(PersonalSpaceBlock)
                .filter(
                    and_(
                        PersonalSpaceBlock.status == "deleted",
                        PersonalSpaceBlock.updated_at < cutoff_date,
                    )
                )
                .delete()
            )

            db.session.commit()

            logging.info(
                f"Cleaned up {deleted_count} deleted blocks older than {days_old} days"
            )
            return deleted_count

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error cleaning up deleted blocks: {str(e)}")
            return 0
