from datetime import datetime
import uuid
from crunevo.extensions import db


class PersonalSpaceTemplate(db.Model):
    __tablename__ = "personal_space_templates"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    template_data = db.Column(db.JSON, nullable=False, default=dict)
    category = db.Column(db.String(100))
    is_public = db.Column(db.Boolean, default=False)
    usage_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="personal_space_templates")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "template_data": self.template_data or {},
            "category": self.category,
            "is_public": self.is_public,
            "usage_count": self.usage_count,
        }
