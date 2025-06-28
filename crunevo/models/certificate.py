
from datetime import datetime
from crunevo.extensions import db


class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    certificate_type = db.Column(db.String(50), nullable=False)  # participacion, misiones, apuntes
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='certificates')
