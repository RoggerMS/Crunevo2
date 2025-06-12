from datetime import datetime
from crunevo.extensions import db

class RankingCache(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    period = db.Column(db.String(10), default='semanal')
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='rankings')
