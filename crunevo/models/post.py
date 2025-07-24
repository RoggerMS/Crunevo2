from datetime import datetime
from crunevo.extensions import db


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    content = db.Column(db.String(280), nullable=False)
    file_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(20))
    edited = db.Column(db.Boolean, default=False)
    comment_permission = db.Column(db.String(10), default="all", nullable=False)
    comments = db.relationship("PostComment", backref="post", lazy=True)
    images = db.relationship(
        "PostImage",
        backref="post",
        lazy=True,
        cascade="all, delete-orphan",
    )
