from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy import and_
from crunevo.models import PersonalSpaceBlock


class AnalyticsService:
    """Service for generating analytics and productivity metrics."""

    @staticmethod
    def get_dashboard_metrics(user_id: int) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics for a user."""
        blocks = PersonalSpaceBlock.query.filter_by(
            user_id=user_id, status="active"
        ).all()

        # Basic counts
        total_blocks = len(blocks)
        active_objectives = len([b for b in blocks if b.type == "objetivo"])

        # Task metrics
        task_blocks = [b for b in blocks if b.type == "tarea"]
        completed_tasks = sum(
            1 for b in task_blocks if (b.metadata_json or {}).get("completed")
        )
        pending_tasks = len(task_blocks) - completed_tasks

        # Productivity score calculation
        productivity_score = AnalyticsService._calculate_productivity_score(user_id)

        # Trends (comparing with previous week)
        trends = AnalyticsService._calculate_trends(user_id)

        return {
            "active_blocks": total_blocks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "active_objectives": active_objectives,
            "productivity_score": productivity_score,
            "trends": trends,
            "last_updated": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def get_productivity_metrics(user_id: int) -> Dict[str, Any]:
        """Get detailed productivity metrics."""
        blocks = PersonalSpaceBlock.query.filter_by(
            user_id=user_id, status="active"
        ).all()

        # Task completion analysis
        task_blocks = [b for b in blocks if b.type == "tarea"]
        completed_tasks = [
            b for b in task_blocks if (b.metadata_json or {}).get("completed")
        ]

        # Objective progress analysis
        objective_blocks = [b for b in blocks if b.type == "objetivo"]
        objective_progress = []
        for obj in objective_blocks:
            progress = (obj.metadata_json or {}).get("progress", 0)
            objective_progress.append(
                {
                    "id": obj.id,
                    "title": obj.title,
                    "progress": progress,
                    "status": (obj.metadata_json or {}).get("status", "no_iniciada"),
                }
            )

        # Weekly activity
        weekly_activity = AnalyticsService._get_weekly_activity(user_id)

        # Block type distribution
        type_distribution = {}
        for block in blocks:
            type_distribution[block.type] = type_distribution.get(block.type, 0) + 1

        return {
            "task_completion": {
                "total_tasks": len(task_blocks),
                "completed_tasks": len(completed_tasks),
                "completion_rate": (
                    round((len(completed_tasks) / len(task_blocks)) * 100, 1)
                    if task_blocks
                    else 0
                ),
                "recent_completions": AnalyticsService._get_recent_completions(user_id),
            },
            "objective_progress": {
                "total_objectives": len(objective_blocks),
                "objectives": objective_progress,
                "average_progress": (
                    round(
                        sum(obj["progress"] for obj in objective_progress)
                        / len(objective_progress),
                        1,
                    )
                    if objective_progress
                    else 0
                ),
            },
            "weekly_activity": weekly_activity,
            "block_distribution": type_distribution,
            "productivity_trends": AnalyticsService._get_productivity_trends(user_id),
        }

    @staticmethod
    def get_goal_tracking(user_id: int) -> Dict[str, Any]:
        """Get goal tracking and progress metrics."""
        objective_blocks = PersonalSpaceBlock.query.filter_by(
            user_id=user_id, type="objetivo", status="active"
        ).all()

        goals = []
        for obj in objective_blocks:
            metadata = obj.metadata_json or {}
            goals.append(
                {
                    "id": obj.id,
                    "title": obj.title,
                    "description": obj.content,
                    "progress": metadata.get("progress", 0),
                    "status": metadata.get("status", "no_iniciada"),
                    "target_date": metadata.get("target_date"),
                    "created_at": obj.created_at.isoformat(),
                    "updated_at": obj.updated_at.isoformat(),
                    "is_overdue": AnalyticsService._is_goal_overdue(metadata),
                }
            )

        # Goal completion stats
        completed_goals = [g for g in goals if g["status"] == "cumplida"]
        in_progress_goals = [g for g in goals if g["status"] == "en_progreso"]
        overdue_goals = [g for g in goals if g["is_overdue"]]

        return {
            "total_goals": len(goals),
            "completed_goals": len(completed_goals),
            "in_progress_goals": len(in_progress_goals),
            "overdue_goals": len(overdue_goals),
            "completion_rate": (
                round((len(completed_goals) / len(goals)) * 100, 1) if goals else 0
            ),
            "goals": goals,
            "monthly_progress": AnalyticsService._get_monthly_goal_progress(user_id),
        }

    @staticmethod
    def _calculate_productivity_score(user_id: int) -> int:
        """Calculate a productivity score based on various factors."""
        blocks = PersonalSpaceBlock.query.filter_by(
            user_id=user_id, status="active"
        ).all()

        if not blocks:
            return 0

        score = 0
        total_weight = 0

        # Task completion weight: 40%
        task_blocks = [b for b in blocks if b.type == "tarea"]
        if task_blocks:
            completed_tasks = sum(
                1 for b in task_blocks if (b.metadata_json or {}).get("completed")
            )
            task_score = (completed_tasks / len(task_blocks)) * 40
            score += task_score
            total_weight += 40

        # Objective progress weight: 30%
        objective_blocks = [b for b in blocks if b.type == "objetivo"]
        if objective_blocks:
            avg_progress = sum(
                (b.metadata_json or {}).get("progress", 0) for b in objective_blocks
            ) / len(objective_blocks)
            objective_score = (avg_progress / 100) * 30
            score += objective_score
            total_weight += 30

        # Recent activity weight: 20%
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_blocks = [b for b in blocks if b.updated_at >= week_ago]
        activity_score = min((len(recent_blocks) / len(blocks)) * 20, 20)
        score += activity_score
        total_weight += 20

        # Block organization weight: 10%
        organization_score = min(
            (len(blocks) / 10) * 10, 10
        )  # Max 10 points for having blocks
        score += organization_score
        total_weight += 10

        return int(score) if total_weight > 0 else 0

    @staticmethod
    def _calculate_trends(user_id: int) -> Dict[str, float]:
        """Calculate trends comparing current week with previous week."""
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)

        # Current week data
        current_blocks = PersonalSpaceBlock.query.filter(
            and_(
                PersonalSpaceBlock.user_id == user_id,
                PersonalSpaceBlock.updated_at >= week_ago,
            )
        ).count()

        # Previous week data
        previous_blocks = PersonalSpaceBlock.query.filter(
            and_(
                PersonalSpaceBlock.user_id == user_id,
                PersonalSpaceBlock.updated_at >= two_weeks_ago,
                PersonalSpaceBlock.updated_at < week_ago,
            )
        ).count()

        # Calculate trends
        blocks_trend = (
            ((current_blocks - previous_blocks) / previous_blocks * 100)
            if previous_blocks > 0
            else 0
        )

        return {
            "blocks_trend": round(blocks_trend, 1),
            "tasks_trend": 0,  # Placeholder for task completion trend
            "objectives_trend": 0,  # Placeholder for objectives trend
            "productivity_trend": 0,  # Placeholder for productivity trend
        }

    @staticmethod
    def _get_weekly_activity(user_id: int) -> List[Dict[str, Any]]:
        """Get activity data for the past 7 days."""
        activity = []
        for i in range(7):
            date = datetime.utcnow() - timedelta(days=i)
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)

            blocks_updated = PersonalSpaceBlock.query.filter(
                and_(
                    PersonalSpaceBlock.user_id == user_id,
                    PersonalSpaceBlock.updated_at >= day_start,
                    PersonalSpaceBlock.updated_at < day_end,
                )
            ).count()

            activity.append(
                {
                    "date": day_start.strftime("%Y-%m-%d"),
                    "day": day_start.strftime("%A"),
                    "blocks_updated": blocks_updated,
                }
            )

        return list(reversed(activity))

    @staticmethod
    def _get_recent_completions(user_id: int) -> List[Dict[str, Any]]:
        """Get recently completed tasks."""
        week_ago = datetime.utcnow() - timedelta(days=7)

        recent_tasks = (
            PersonalSpaceBlock.query.filter(
                and_(
                    PersonalSpaceBlock.user_id == user_id,
                    PersonalSpaceBlock.type == "tarea",
                    PersonalSpaceBlock.updated_at >= week_ago,
                )
            )
            .order_by(PersonalSpaceBlock.updated_at.desc())
            .limit(10)
            .all()
        )

        completions = []
        for task in recent_tasks:
            if (task.metadata_json or {}).get("completed"):
                completions.append(
                    {
                        "id": task.id,
                        "title": task.title,
                        "completed_at": task.updated_at.isoformat(),
                    }
                )

        return completions

    @staticmethod
    def _get_productivity_trends(user_id: int) -> Dict[str, Any]:
        """Get productivity trends over time."""
        # This is a simplified version - in a real app you'd store historical data
        return {
            "daily_scores": [],
            "weekly_average": 0,
            "monthly_average": 0,
            "trend_direction": "stable",
        }

    @staticmethod
    def _is_goal_overdue(metadata: Dict[str, Any]) -> bool:
        """Check if a goal is overdue based on target date."""
        target_date_str = metadata.get("target_date")
        if not target_date_str:
            return False

        try:
            target_date = datetime.fromisoformat(target_date_str.replace("Z", "+00:00"))
            return (
                target_date < datetime.utcnow() and metadata.get("status") != "cumplida"
            )
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def _get_monthly_goal_progress(user_id: int) -> List[Dict[str, Any]]:
        """Get goal progress for the past 6 months."""
        monthly_data = []
        for i in range(6):
            # Calculate month start/end
            current_date = datetime.utcnow().replace(day=1) - timedelta(days=i * 30)
            month_start = current_date.replace(day=1)
            next_month = (
                month_start.replace(month=month_start.month + 1)
                if month_start.month < 12
                else month_start.replace(year=month_start.year + 1, month=1)
            )

            # Count goals created/completed in this month
            goals_created = PersonalSpaceBlock.query.filter(
                and_(
                    PersonalSpaceBlock.user_id == user_id,
                    PersonalSpaceBlock.type == "objetivo",
                    PersonalSpaceBlock.created_at >= month_start,
                    PersonalSpaceBlock.created_at < next_month,
                )
            ).count()

            monthly_data.append(
                {
                    "month": month_start.strftime("%Y-%m"),
                    "month_name": month_start.strftime("%B %Y"),
                    "goals_created": goals_created,
                    "goals_completed": 0,  # Placeholder - would need completion tracking
                }
            )

        return list(reversed(monthly_data))
