from datetime import datetime
from crunevo.extensions import db


class ProductLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    action = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    product = db.relationship("Product", backref="logs")
    admin = db.relationship("User")
