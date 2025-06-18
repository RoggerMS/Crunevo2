from datetime import datetime
from crunevo.extensions import db


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column("timestamp", db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    note_id = db.Column(db.Integer, db.ForeignKey("note.id"))
