from datetime import datetime
from crunevo.extensions import db


class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    career = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    avatar_url = db.Column(db.String(255))
    member_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    members = db.relationship("ClubMember", backref="club", lazy=True)


class ClubMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey("club.id"), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(20), default="member")  # member, moderator, admin

    # Relationships
    user = db.relationship("User")
