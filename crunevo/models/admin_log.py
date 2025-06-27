from datetime import datetime
from crunevo.extensions import db


class AdminLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.Integer)
    target_type = db.Column(db.String(30))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    admin = db.relationship("User")
