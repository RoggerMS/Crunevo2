from crunevo.extensions import db


class SiteConfig(db.Model):
    """Simple key/value site configuration storage."""

    __tablename__ = "site_config"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255))
