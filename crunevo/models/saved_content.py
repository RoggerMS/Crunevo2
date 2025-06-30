from datetime import datetime
from crunevo.extensions import db


class SavedContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    content_type = db.Column(db.String(20), nullable=False)  # 'note', 'post'
    content_id = db.Column(db.Integer, nullable=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship("User", backref="saved_contents")

    # Composite unique constraint
    __table_args__ = (db.UniqueConstraint("user_id", "content_type", "content_id"),)
