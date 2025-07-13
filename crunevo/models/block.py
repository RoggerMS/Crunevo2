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

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "block_type": self.type,
            "title": self.title,
            "content": self.content,
            "metadata": self.get_metadata(),
            "order_index": self.order_index,
            "is_featured": self.is_featured,
        }
