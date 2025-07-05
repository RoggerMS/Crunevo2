from datetime import datetime
from crunevo.extensions import db


class GroupMission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    goal = db.Column(db.Integer, default=1)
    credit_reward = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    participants = db.relationship(
        "GroupMissionParticipant",
        backref="group_mission",
        cascade="all, delete-orphan",
    )


class GroupMissionParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    group_mission_id = db.Column(
        db.Integer, db.ForeignKey("group_mission.id"), nullable=False
    )
    progress = db.Column(db.Integer, default=0)
    claimed = db.Column(db.Boolean, default=False)

    user = db.relationship("User")
