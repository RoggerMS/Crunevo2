from datetime import datetime
from crunevo.extensions import db


class AcademicTeam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    avatar_url = db.Column(db.String(255), default="/static/img/default_team.png")
    captain_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    captain = db.relationship("User", backref="captained_teams")
    members = db.relationship("TeamMember", backref="team", lazy="dynamic")

    @property
    def member_count(self):
        return self.members.filter_by(is_active=True).count()

    @property
    def can_accept_members(self):
        return self.member_count < 5


class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("academic_team.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    points_contributed = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    user = db.relationship("User", backref="team_memberships")


class LeagueMonth(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    winner_team_id = db.Column(db.Integer, db.ForeignKey("academic_team.id"))
    is_active = db.Column(db.Boolean, default=True)

    winner_team = db.relationship("AcademicTeam")


class TeamAction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("academic_team.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    action_type = db.Column(
        db.String(50), nullable=False
    )  # note_upload, mission_complete, etc
    points_earned = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    team = db.relationship("AcademicTeam")
    user = db.relationship("User")
