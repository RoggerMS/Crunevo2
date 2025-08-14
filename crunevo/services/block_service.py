from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy import func, and_, or_
from crunevo.extensions import db
from crunevo.models import PersonalSpaceBlock
from crunevo.services.validation_service import ValidationService
from crunevo.services.cache_service import CacheInvalidator


class BlockService:
    """Service for managing personal space blocks with advanced functionality."""

    @staticmethod
    def create_block(user_id: int, block_data: Dict[str, Any]) -> PersonalSpaceBlock:
        """Create a new block with validation and auto-ordering."""
        # Validate input data
        validation_result = ValidationService.validate_block_data(block_data)
        if not validation_result["valid"]:
            raise ValueError(
                f"Validation errors: {', '.join(validation_result['errors'])}"
            )

        cleaned_data = validation_result["cleaned_data"]

        # Get next order index
        max_order = (
            db.session.query(func.max(PersonalSpaceBlock.order_index))
            .filter_by(user_id=user_id)
            .scalar()
            or 0
        )

        # Create block with defaults
        block = PersonalSpaceBlock(
            user_id=user_id,
            type=cleaned_data["type"],
            title=cleaned_data.get("title", f"Nuevo {cleaned_data['type']}"),
            content=cleaned_data.get("content", ""),
            metadata_json=cleaned_data.get("metadata", {}),
            order_index=max_order + 1,
            status="active",
        )

        # Apply type-specific defaults
        BlockService._apply_type_defaults(block)

        db.session.add(block)
        db.session.commit()

        # Invalidate cache
        CacheInvalidator.on_block_change(user_id)

        return block

    @staticmethod
    def _apply_type_defaults(block: PersonalSpaceBlock) -> None:
        """Apply default metadata based on block type."""
        metadata = block.metadata_json or {}

        if block.type == "tarea":
            metadata.setdefault("completed", False)
            metadata.setdefault("priority", "medium")
            metadata.setdefault("due_date", None)
        elif block.type == "objetivo":
            metadata.setdefault("progress", 0)
            metadata.setdefault("target_date", None)
            metadata.setdefault("status", "no_iniciada")
        elif block.type == "lista":
            metadata.setdefault("tasks", [])
        elif block.type == "kanban":
            metadata.setdefault(
                "columns", {"por_hacer": [], "en_progreso": [], "hecho": []}
            )
        elif block.type == "recordatorio":
            metadata.setdefault("due_date", None)
            metadata.setdefault("priority", "medium")

        block.metadata_json = metadata

    @staticmethod
    def update_block(
        block_id: str, user_id: int, update_data: Dict[str, Any]
    ) -> PersonalSpaceBlock:
        """Update a block with validation."""
        block = PersonalSpaceBlock.query.filter_by(id=block_id, user_id=user_id).first()

        if not block:
            raise ValueError("Block not found")

        # Validate update data
        current_data = {
            "type": block.type,
            "title": update_data.get("title", block.title),
            "content": update_data.get("content", block.content),
            "metadata": update_data.get("metadata", block.metadata_json or {}),
        }

        validation_result = ValidationService.validate_block_data(current_data)
        if not validation_result["valid"]:
            raise ValueError(
                f"Validation errors: {', '.join(validation_result['errors'])}"
            )

        cleaned_data = validation_result["cleaned_data"]

        # Update fields
        for field in ["title", "content", "status", "is_featured"]:
            if field in update_data:
                if field in cleaned_data:
                    setattr(block, field, cleaned_data[field])
                else:
                    setattr(block, field, update_data[field])

        # Update metadata
        if "metadata" in update_data:
            block.metadata_json = cleaned_data["metadata"]

        block.updated_at = datetime.utcnow()
        db.session.commit()

        # Invalidate cache
        CacheInvalidator.on_block_change(user_id)

        return block

    @staticmethod
    def delete_block(block_id: str, user_id: int) -> bool:
        """Soft delete a block by moving to trash."""
        block = PersonalSpaceBlock.query.filter_by(id=block_id, user_id=user_id).first()

        if not block:
            return False

        block.status = "deleted"
        block.updated_at = datetime.utcnow()
        db.session.commit()

        # Invalidate cache
        CacheInvalidator.on_block_change(user_id)

        return True

    @staticmethod
    def reorder_blocks(user_id: int, block_orders: List[Dict[str, Any]]) -> bool:
        """Reorder blocks based on provided order list."""
        try:
            for item in block_orders:
                idx = item.get("order_index", item.get("position"))
                block = PersonalSpaceBlock.query.filter_by(
                    id=item.get("id"), user_id=user_id
                ).first()
                if block is not None and idx is not None:
                    block.order_index = idx

            db.session.commit()
            CacheInvalidator.on_block_change(user_id)
            return True
        except Exception:
            db.session.rollback()
            return False

    @staticmethod
    def get_block(block_id: str, user_id: int) -> Optional[PersonalSpaceBlock]:
        """Get a specific block by ID and user ID."""
        return PersonalSpaceBlock.query.filter_by(
            id=block_id, user_id=user_id, status="active"
        ).first()

    @staticmethod
    def get_user_blocks(
        user_id: int, status: str = "active", block_type: Optional[str] = None
    ) -> List[PersonalSpaceBlock]:
        """Get user blocks with optional filtering."""
        query = PersonalSpaceBlock.query.filter_by(user_id=user_id, status=status)

        if block_type:
            query = query.filter_by(type=block_type)

        return query.order_by(PersonalSpaceBlock.order_index.asc()).all()

    @staticmethod
    def search_blocks(user_id: int, search_term: str) -> List[PersonalSpaceBlock]:
        """Search blocks by title and content."""
        search_pattern = f"%{search_term}%"
        return (
            PersonalSpaceBlock.query.filter(
                and_(
                    PersonalSpaceBlock.user_id == user_id,
                    PersonalSpaceBlock.status == "active",
                    or_(
                        PersonalSpaceBlock.title.ilike(search_pattern),
                        PersonalSpaceBlock.content.ilike(search_pattern),
                    ),
                )
            )
            .order_by(PersonalSpaceBlock.updated_at.desc())
            .all()
        )

    @staticmethod
    def duplicate_block(block_id: str, user_id: int) -> Optional[PersonalSpaceBlock]:
        """Create a duplicate of an existing block."""
        original = PersonalSpaceBlock.query.filter_by(
            id=block_id, user_id=user_id
        ).first()

        if not original:
            return None

        # Get next order index
        max_order = (
            db.session.query(func.max(PersonalSpaceBlock.order_index))
            .filter_by(user_id=user_id)
            .scalar()
            or 0
        )

        # Create duplicate
        duplicate = PersonalSpaceBlock(
            user_id=user_id,
            type=original.type,
            title=f"{original.title} (Copia)",
            content=original.content,
            metadata_json=(
                original.metadata_json.copy() if original.metadata_json else {}
            ),
            order_index=max_order + 1,
            status="active",
        )

        db.session.add(duplicate)
        db.session.commit()
        return duplicate

    @staticmethod
    def get_block_analytics(user_id: int) -> Dict[str, Any]:
        """Get analytics data for user's blocks."""
        blocks = PersonalSpaceBlock.query.filter_by(
            user_id=user_id, status="active"
        ).all()

        # Count by type
        type_counts = {}
        for block in blocks:
            type_counts[block.type] = type_counts.get(block.type, 0) + 1

        # Task completion stats
        task_blocks = [b for b in blocks if b.type == "tarea"]
        completed_tasks = sum(
            1 for b in task_blocks if (b.metadata_json or {}).get("completed")
        )

        # Objective progress
        objective_blocks = [b for b in blocks if b.type == "objetivo"]
        avg_objective_progress = 0
        if objective_blocks:
            total_progress = sum(
                (b.metadata_json or {}).get("progress", 0) for b in objective_blocks
            )
            avg_objective_progress = total_progress / len(objective_blocks)

        # Recent activity
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_blocks = [b for b in blocks if b.updated_at >= week_ago]

        return {
            "total_blocks": len(blocks),
            "blocks_by_type": type_counts,
            "task_completion": {
                "total": len(task_blocks),
                "completed": completed_tasks,
                "percentage": (
                    int((completed_tasks / len(task_blocks)) * 100)
                    if task_blocks
                    else 0
                ),
            },
            "objective_progress": {
                "total": len(objective_blocks),
                "average_progress": round(avg_objective_progress, 1),
            },
            "recent_activity": {"blocks_updated_this_week": len(recent_blocks)},
        }
