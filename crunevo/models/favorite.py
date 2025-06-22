from datetime import datetime
from crunevo.extensions import db


class FavoriteProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
