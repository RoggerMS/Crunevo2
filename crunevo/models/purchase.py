from datetime import datetime
from crunevo.extensions import db


class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price_soles = db.Column(db.Numeric(10, 2))
    price_credits = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    shipping_address = db.Column(db.String(255))
    shipping_message = db.Column(db.Text)

    user = db.relationship("User")
    product = db.relationship("Product")

    # Backwards compatible aliases

    @property
    def price_paid(self) -> float:
        """Return the amount paid in soles."""
        return self.price_soles

    @price_paid.setter
    def price_paid(self, value: float) -> None:
        self.price_soles = value

    @property
    def credits_used(self) -> int:
        """Return the credits spent."""
        return self.price_credits

    @credits_used.setter
    def credits_used(self, value: int) -> None:
        self.price_credits = value
