from datetime import datetime
import secrets
from crunevo.extensions import db


class TwoFactorToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    secret = db.Column(
        db.String(32), nullable=False, default=lambda: secrets.token_hex(10)
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    backup_codes = db.Column(db.Text)  # comma-separated codes

    user = db.relationship("User", backref=db.backref("two_factor", uselist=False))
