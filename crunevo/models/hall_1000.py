
from datetime import datetime
from crunevo.extensions import db


class CrolarsHallMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    total_spent = db.Column(db.Integer, default=0)
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    access_level = db.Column(db.String(20), default='bronze')  # bronze, silver, gold, platinum
    premium_downloads = db.Column(db.Integer, default=0)
    raffle_entries = db.Column(db.Integer, default=0)
    
    user = db.relationship('User', backref=db.backref('hall_membership', uselist=False))


class PremiumContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    content_type = db.Column(db.String(50), nullable=False)  # course, note, video, etc
    file_url = db.Column(db.String(500))
    thumbnail_url = db.Column(db.String(500))
    required_level = db.Column(db.String(20), default='bronze')
    download_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class HallRaffle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    prize_description = db.Column(db.Text, nullable=False)
    entry_cost = db.Column(db.Integer, default=1)  # raffle entries needed
    max_participants = db.Column(db.Integer, default=100)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    winner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_active = db.Column(db.Boolean, default=True)
    is_completed = db.Column(db.Boolean, default=False)
    
    winner = db.relationship('User', backref='won_raffles')
    participants = db.relationship('RaffleParticipant', backref='raffle', lazy='dynamic')


class RaffleParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    raffle_id = db.Column(db.Integer, db.ForeignKey('hall_raffle.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    entries_used = db.Column(db.Integer, default=1)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='raffle_participations')
