from datetime import datetime
from crunevo.extensions import db


class Mission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    goal = db.Column(db.Integer, default=1)
    credit_reward = db.Column(db.Integer, default=0)
    achievement_code = db.Column(db.String(50))


class UserMission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    mission_id = db.Column(db.Integer, db.ForeignKey("mission.id"), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="missions")
    mission = db.relationship("Mission")
