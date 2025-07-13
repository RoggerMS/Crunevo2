from datetime import datetime
from crunevo.extensions import db


class Block(db.Model):
    __tablename__ = "blocks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), default="Nuevo bloque")
    content = db.Column(db.Text)
    metadata_json = db.Column("metadata", db.JSON, default={})
    is_featured = db.Column(db.Boolean, default=False)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = db.relationship("User", backref="blocks")

    def get_metadata(self):
        return self.metadata_json or {}

    def set_metadata(self, value):
        self.metadata_json = value or {}

    def get_progress_percentage(self):
        """Calculate completion percentage based on block type."""
        metadata = self.get_metadata()

        if self.type == "lista":
            tasks = metadata.get("tasks", [])
            if not tasks:
                return 0
            completed = sum(1 for task in tasks if task.get("completed", False))
            return int((completed / len(tasks)) * 100)

        if self.type in {"meta", "objetivo"}:
            return metadata.get("progress", 0)

        if self.type == "kanban":
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

    def is_overdue(self):
        """Check if reminder block is overdue based on due_date."""
        if self.type != "recordatorio":
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
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "content": self.content,
            "metadata": self.get_metadata(),
            "order_index": self.order_index,
            "is_featured": self.is_featured,
        }
