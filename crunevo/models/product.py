from crunevo.extensions import db


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    price_credits = db.Column(db.Integer)
    image = db.Column(db.String(200))
    image_urls = db.Column(db.JSON)
    stock = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    credits_only = db.Column(db.Boolean, default=False)
    is_popular = db.Column(db.Boolean, default=False)
    is_new = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(50))
    download_url = db.Column(db.String(255))
    allow_multiple = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=True)

    @property
    def first_image(self) -> str | None:
        """Return the first image URL available."""
        if self.image_urls:
            return self.image_urls[0]
        return self.image
