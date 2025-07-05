from datetime import datetime
from crunevo.extensions import db


class PrintRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    note_id = db.Column(db.Integer, db.ForeignKey("note.id"), nullable=False)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    fulfilled = db.Column(db.Boolean, default=False)
    fulfilled_at = db.Column(db.DateTime)

    user = db.relationship("User")
    note = db.relationship("Note")
