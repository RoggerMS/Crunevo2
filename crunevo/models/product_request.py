from datetime import datetime
from crunevo.extensions import db


class ProductRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(140), nullable=False)
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    price_soles = db.Column(db.Numeric(10, 2))
    image_url = db.Column(db.String(255))
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = db.relationship("User")
