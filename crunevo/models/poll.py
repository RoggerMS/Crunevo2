
from datetime import datetime
from crunevo.extensions import db


class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(120), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    total_votes = db.Column(db.Integer, default=0)
    
    # Relationships
    author = db.relationship("User", backref="polls")
    options = db.relationship("PollOption", backref="poll", lazy=True, cascade="all, delete-orphan")
    votes = db.relationship("PollVote", backref="poll", lazy=True, cascade="all, delete-orphan")

    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    def get_results(self):
        if self.total_votes == 0:
            return [(option, 0) for option in self.options]
        return [(option, (option.vote_count / self.total_votes) * 100) for option in self.options]


class PollOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"), nullable=False)
    text = db.Column(db.String(80), nullable=False)
    vote_count = db.Column(db.Integer, default=0)
    
    # Relationships
    votes = db.relationship("PollVote", backref="option", lazy=True, cascade="all, delete-orphan")


class PollVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey("poll_option.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    voted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship("User")
