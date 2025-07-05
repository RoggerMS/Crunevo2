from datetime import datetime
from crunevo.extensions import db


class PageView(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(300), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
