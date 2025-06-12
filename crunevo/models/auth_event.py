from datetime import datetime

from crunevo.extensions import db


class AuthEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    event_type = db.Column(db.String(20), nullable=False)
    ip = db.Column(db.String(45))
    ua = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="auth_events")
