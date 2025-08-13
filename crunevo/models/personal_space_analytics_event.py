from datetime import datetime
import uuid
from crunevo.extensions import db


class PersonalSpaceAnalyticsEvent(db.Model):
    __tablename__ = "personal_space_analytics_events"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    event_data = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="personal_space_analytics_events")

    def to_dict(self):
        return {
            "id": self.id,
            "event_type": self.event_type,
            "event_data": self.event_data or {},
            "created_at": self.created_at.isoformat(),
        }
