from datetime import datetime
from crunevo.extensions import db


class Credit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    amount = db.Column(db.Numeric(scale=2), nullable=False)
    reason = db.Column(db.String(50), nullable=False)
    related_id = db.Column(db.Integer, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="credit_history")
