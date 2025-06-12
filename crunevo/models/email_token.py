from datetime import datetime
from uuid import uuid4
from crunevo.extensions import db


class EmailToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(
        db.String(64), unique=True, nullable=False, default=lambda: uuid4().hex
    )
    email = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    consumed_at = db.Column(db.DateTime)

    user = db.relationship("User", backref="email_tokens")
