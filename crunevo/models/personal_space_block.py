from datetime import datetime
import uuid
from crunevo.extensions import db


class PersonalSpaceBlock(db.Model):
    __tablename__ = "personal_space_blocks"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False, default="")
    content = db.Column(db.Text)
    metadata_json = db.Column("metadata", db.JSON, default=dict)
    order_index = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref="personal_space_blocks")

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "content": self.content,
            "metadata": self.metadata_json or {},
            "order_index": self.order_index,
            "status": self.status,
        }

    def get_metadata(self):
        return self.metadata_json or {}

    def set_metadata(self, value):
        self.metadata_json = value or {}


PersonalSpaceBlock.metadata = property(
    PersonalSpaceBlock.get_metadata, PersonalSpaceBlock.set_metadata
)
