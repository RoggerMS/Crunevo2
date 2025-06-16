from datetime import datetime
from crunevo.extensions import db


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, default="")
    filename = db.Column(db.String(200), default="")
    tags = db.Column(db.String(200), default="")
    category = db.Column(db.String(100), default="")
    views = db.Column(db.Integer, default=0)
    downloads = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    comments = db.relationship("Comment", backref="note", lazy=True)
