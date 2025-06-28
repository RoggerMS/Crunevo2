
from datetime import datetime
from crunevo.extensions import db


class EventParticipation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    attended = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', backref='event_participations')
    event = db.relationship('Event', backref='participants')
