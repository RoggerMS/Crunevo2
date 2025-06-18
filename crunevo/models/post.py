from datetime import datetime
from crunevo.extensions import db


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    content = db.Column(db.String(280), nullable=False)
    file_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.Column(db.Integer, default=0)
    type = db.Column(db.String(20))
