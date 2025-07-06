from datetime import datetime
from crunevo.extensions import db
import json


class PersonalBlock(db.Model):
    __tablename__ = "personal_block"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    block_type = db.Column(
        db.String(50), nullable=False
    )  # nota, lista, meta, recordatorio, frase, enlace, tarea, kanban, objetivo
    title = db.Column(db.String(200), default="")
    content = db.Column(db.Text, default="")
    _metadata = db.Column(
        "metadata", db.Text, default="{}"
    )  # JSON for flexible data storage
    order_position = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    color = db.Column(db.String(20), default="indigo")
    icon = db.Column(db.String(50), default="bi-card-text")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship to user
    user = db.relationship("User", backref="personal_blocks")

    def get_metadata(self):
        """Parse metadata JSON safely"""
        try:
            return json.loads(self.metadata) if self.metadata else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_metadata(self, data):
        """Set metadata as JSON"""
        self.metadata = json.dumps(data) if data else "{}"

    def get_progress_percentage(self):
        """Calculate progress for goals and task lists"""
        metadata = self.get_metadata()

        if self.block_type == "lista":
            tasks = metadata.get("tasks", [])
            if not tasks:
                return 0
            completed = sum(1 for task in tasks if task.get("completed", False))
            return int((completed / len(tasks)) * 100)

        elif self.block_type == "meta" or self.block_type == "objetivo":
            return metadata.get("progress", 0)

        elif self.block_type == "kanban":
            columns = metadata.get("columns", {})
            total_tasks = 0
            completed_tasks = 0
            for column_name, tasks in columns.items():
                if column_name.lower() in ["hecho", "completado", "finalizado"]:
                    completed_tasks += len(tasks)
                total_tasks += len(tasks)

            if total_tasks == 0:
                return 0
            return int((completed_tasks / total_tasks) * 100)

        return 0

    def get_priority_color(self):
        """Get color based on priority or type"""
        metadata = self.get_metadata()
        priority = metadata.get("priority", "medium")

        priority_colors = {"high": "red", "medium": "amber", "low": "green"}

        return priority_colors.get(priority, self.color)

    def get_status_badge(self):
        """Get status badge for different block types"""
        metadata = self.get_metadata()

        if self.block_type == "objetivo":
            status = metadata.get("status", "no_iniciada")
            status_map = {
                "no_iniciada": {"text": "No iniciada", "color": "gray"},
                "en_progreso": {"text": "En progreso", "color": "blue"},
                "cumplida": {"text": "Cumplida", "color": "green"},
                "vencida": {"text": "Vencida", "color": "red"},
            }
            return status_map.get(status, status_map["no_iniciada"])

        elif self.block_type == "tarea":
            if metadata.get("completed", False):
                return {"text": "Completada", "color": "green"}
            elif self.is_overdue():
                return {"text": "Vencida", "color": "red"}
            else:
                return {"text": "Pendiente", "color": "blue"}

        return {"text": "Activo", "color": "blue"}

    def get_due_days(self):
        """Get days until due date"""
        metadata = self.get_metadata()
        due_date_str = metadata.get("due_date") or metadata.get("deadline")

        if not due_date_str:
            return None

        try:
            due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
            diff = due_date - datetime.utcnow()
            return diff.days
        except (ValueError, AttributeError):
            return None

    def is_overdue(self):
        """Check if reminder is overdue"""
        if self.block_type != "recordatorio":
            return False

        metadata = self.get_metadata()
        due_date_str = metadata.get("due_date")

        if not due_date_str:
            return False

        try:
            due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
            return due_date < datetime.utcnow()
        except (ValueError, AttributeError):
            return False

    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            "id": self.id,
            "block_type": self.block_type,
            "title": self.title,
            "content": self.content,
            "metadata": self.get_metadata(),
            "order_position": self.order_position,
            "is_featured": self.is_featured,
            "color": self.color,
            "icon": self.icon,
            "progress": self.get_progress_percentage(),
            "is_overdue": self.is_overdue(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# expose metadata attribute without conflicting with SQLAlchemy base
def _get_metadata(self):
    return self._metadata


def _set_metadata(self, value):
    self._metadata = value


PersonalBlock.metadata = property(_get_metadata, _set_metadata)
