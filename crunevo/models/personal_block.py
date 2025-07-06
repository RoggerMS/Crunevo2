
from datetime import datetime
from crunevo.extensions import db
import json


class PersonalBlock(db.Model):
    __tablename__ = 'personal_block'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    block_type = db.Column(db.String(50), nullable=False)  # nota, lista, meta, recordatorio, frase, enlace
    title = db.Column(db.String(200), default="")
    content = db.Column(db.Text, default="")
    metadata = db.Column(db.Text, default="{}")  # JSON for flexible data storage
    order_position = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    color = db.Column(db.String(20), default="indigo")
    icon = db.Column(db.String(50), default="bi-card-text")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to user
    user = db.relationship('User', backref='personal_blocks')
    
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
        
        if self.block_type == 'lista':
            tasks = metadata.get('tasks', [])
            if not tasks:
                return 0
            completed = sum(1 for task in tasks if task.get('completed', False))
            return int((completed / len(tasks)) * 100)
        
        elif self.block_type == 'meta':
            return metadata.get('progress', 0)
        
        return 0
    
    def is_overdue(self):
        """Check if reminder is overdue"""
        if self.block_type != 'recordatorio':
            return False
        
        metadata = self.get_metadata()
        due_date_str = metadata.get('due_date')
        
        if not due_date_str:
            return False
        
        try:
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
            return due_date < datetime.utcnow()
        except (ValueError, AttributeError):
            return False
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'id': self.id,
            'block_type': self.block_type,
            'title': self.title,
            'content': self.content,
            'metadata': self.get_metadata(),
            'order_position': self.order_position,
            'is_featured': self.is_featured,
            'color': self.color,
            'icon': self.icon,
            'progress': self.get_progress_percentage(),
            'is_overdue': self.is_overdue(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
