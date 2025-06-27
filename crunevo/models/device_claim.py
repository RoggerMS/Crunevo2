from datetime import datetime
from crunevo.extensions import db


class DeviceClaim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_token = db.Column(db.String(255), index=True, nullable=False)
    mission_code = db.Column(db.String(50), index=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")
