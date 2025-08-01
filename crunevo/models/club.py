from datetime import datetime
from crunevo.extensions import db


class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    career = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    avatar_url = db.Column(db.String(255))
    banner_url = db.Column(db.String(255))  # New field for club banner
    facebook_url = db.Column(db.String(255))  # New field for Facebook link
    whatsapp_url = db.Column(db.String(255))  # New field for WhatsApp link
    creator_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False
    )  # New field for creator
    member_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    members = db.relationship("ClubMember", backref="club", lazy=True)
    creator = db.relationship("User", backref="created_clubs")  # New relationship

    def is_creator(self, user):
        """Check if the given user is the creator of this club"""
        return self.creator_id == user.id if user and user.is_authenticated else False

    def get_creator_membership(self):
        """Get the creator's membership record (should be admin)"""
        return ClubMember.query.filter_by(
            user_id=self.creator_id, club_id=self.id
        ).first()


class ClubMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey("club.id"), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(20), default="member")  # member, moderator, admin

    # Relationships
    user = db.relationship("User")
