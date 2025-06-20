from datetime import datetime
from crunevo.extensions import db


class AdminNotification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    admin = db.relationship("User")
