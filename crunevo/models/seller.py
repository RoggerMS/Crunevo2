from datetime import datetime
from crunevo.extensions import db


class Seller(db.Model):
    """Modelo para vendedores en el marketplace."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    store_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    logo = db.Column(db.String(200))
    banner = db.Column(db.String(200))
    contact_email = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    rating = db.Column(db.Float, default=0.0)
    total_ratings = db.Column(db.Integer, default=0)
    total_sales = db.Column(db.Integer, default=0)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = db.relationship("User", backref=db.backref("seller", uselist=False))
    products = db.relationship("Product", backref="seller", lazy="dynamic")
    
    def __repr__(self):
        return f"<Seller {self.store_name}>"