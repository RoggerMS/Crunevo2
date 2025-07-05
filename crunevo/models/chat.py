from datetime import datetime
from crunevo.extensions import db


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    receiver_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=True
    )  # None para chat global
    content = db.Column(db.Text, nullable=False)
    attachment_url = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_global = db.Column(db.Boolean, default=False)
    is_read = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)

    # Relaciones
    sender = db.relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    receiver = db.relationship(
        "User", foreign_keys=[receiver_id], backref="received_messages"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "sender_username": self.sender.username if self.sender else None,
            "receiver_id": self.receiver_id,
            "receiver_username": self.receiver.username if self.receiver else None,
            "content": self.content,
            "attachment_url": self.attachment_url,
            "timestamp": self.timestamp.isoformat(),
            "is_global": self.is_global,
            "is_read": self.is_read,
        }


class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))

    creator = db.relationship("User", backref="created_rooms")
