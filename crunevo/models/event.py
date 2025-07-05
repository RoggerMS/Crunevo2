from datetime import datetime
from crunevo.extensions import db


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    image_url = db.Column(db.String(255))
    is_featured = db.Column(db.Boolean, default=False)
    rewards = db.Column(db.Text)  # JSON string with reward details
    category = db.Column(db.String(50))
    jitsi_url = db.Column(db.String(255))
    zoom_url = db.Column(db.String(255))
    notification_times = db.Column(db.JSON)
    recurring = db.Column(db.String(20))

    @property
    def is_upcoming(self):
        return self.event_date > datetime.utcnow()

    @property
    def formatted_date(self):
        return self.event_date.strftime("%d de %B")
