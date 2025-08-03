from datetime import datetime

from crunevo import db
from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property


class Seller(db.Model):
    __tablename__ = "marketplace_sellers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    store_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    logo_image = db.Column(db.String(255))
    banner_image = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    location = db.Column(db.String(100))
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = db.relationship("User", backref=db.backref("seller", uselist=False))
    products = db.relationship("MarketplaceProduct", backref="seller", lazy="dynamic")

    @hybrid_property
    def rating(self):
        """Calculate the average rating from all seller's products"""
        from crunevo.models.product import Review

        product_ids = [p.id for p in self.products.all()]
        if not product_ids:
            return 0

        avg_rating = (
            db.session.query(func.avg(Review.rating))
            .filter(Review.product_id.in_(product_ids))
            .scalar()
        )

        return round(avg_rating or 0, 1)

    @hybrid_property
    def total_sales(self):
        """Count the total number of sales for this seller"""
        return sum(product.total_sales for product in self.products)

    @hybrid_property
    def total_revenue(self):
        """Calculate the total revenue for this seller"""
        return sum(product.total_revenue for product in self.products)

    def __repr__(self):
        return f"<Seller {self.store_name}>"


class MarketplaceProduct(db.Model):
    __tablename__ = "marketplace_products"

    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(
        db.Integer, db.ForeignKey("marketplace_sellers.id"), nullable=False
    )
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=1)
    category_id = db.Column(db.Integer, db.ForeignKey("product_categories.id"))
    subcategory_id = db.Column(db.Integer, db.ForeignKey("product_subcategories.id"))
    condition = db.Column(db.String(20), default="new")  # new, used, refurbished
    shipping_cost = db.Column(db.Float, default=0)
    shipping_time = db.Column(db.String(50))
    free_shipping = db.Column(db.Boolean, default=False)
    warranty = db.Column(db.String(100))
    tags = db.Column(db.String(255))
    views = db.Column(db.Integer, default=0)
    is_approved = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default="pending")  # pending, approved, rejected
    rejection_reason = db.Column(db.Text)
    is_new = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    category = db.relationship("ProductCategory")
    subcategory = db.relationship("ProductSubcategory")
    images = db.relationship(
        "MarketplaceProductImage", backref="product", cascade="all, delete-orphan"
    )
    sales = db.relationship("MarketplaceProductSale", backref="product", lazy="dynamic")

    @hybrid_property
    def main_image(self):
        """Get the main image for this product"""
        first_image = MarketplaceProductImage.query.filter_by(
            product_id=self.id
        ).first()
        if first_image:
            return first_image.image_path
        return "default_product.jpg"

    @hybrid_property
    def total_sales(self):
        """Count the total number of sales for this product"""
        return self.sales.count()

    @hybrid_property
    def total_revenue(self):
        """Calculate the total revenue for this product"""
        return sum(sale.quantity * self.price for sale in self.sales)

    def __repr__(self):
        return f"<MarketplaceProduct {self.name}>"


class MarketplaceProductImage(db.Model):
    __tablename__ = "marketplace_product_images"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("marketplace_products.id"), nullable=False
    )
    image_path = db.Column(db.String(255), nullable=False)
    is_main = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MarketplaceProductImage {self.image_path}>"


class MarketplaceProductSale(db.Model):
    __tablename__ = "marketplace_product_sales"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("marketplace_products.id"), nullable=False
    )
    buyer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)  # Price at the time of purchase
    status = db.Column(
        db.String(20), default="completed"
    )  # pending, completed, cancelled, refunded
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    buyer = db.relationship("User")

    def __repr__(self):
        return f"<MarketplaceProductSale {self.id}>"


class MarketplaceConversation(db.Model):
    __tablename__ = "marketplace_conversations"

    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("marketplace_products.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user1 = db.relationship("User", foreign_keys=[user1_id])
    user2 = db.relationship("User", foreign_keys=[user2_id])
    product = db.relationship("MarketplaceProduct")
    messages = db.relationship(
        "MarketplaceMessage",
        backref="conversation",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="MarketplaceMessage.created_at",
    )

    @hybrid_property
    def last_message(self):
        """Get the last message in this conversation"""
        return self.messages.order_by(MarketplaceMessage.created_at.desc()).first()

    def get_other_user(self, user_id):
        """Get the other user in the conversation"""
        if self.user1_id == user_id:
            return self.user2
        return self.user1

    def __repr__(self):
        return f"<MarketplaceConversation {self.id}>"


class MarketplaceMessage(db.Model):
    __tablename__ = "marketplace_messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer, db.ForeignKey("marketplace_conversations.id"), nullable=False
    )
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sender = db.relationship("User")

    def __repr__(self):
        return f"<MarketplaceMessage {self.id}>"
