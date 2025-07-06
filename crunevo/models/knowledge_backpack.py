from datetime import datetime
from crunevo.extensions import db


class KnowledgeBackpack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True
    )
    journal_content = db.Column(db.Text, default="")
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    total_notes = db.Column(db.Integer, default=0)
    total_courses = db.Column(db.Integer, default=0)
    total_missions = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship(
        "User", backref=db.backref("knowledge_backpack", uselist=False)
    )


class LearningEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    backpack_id = db.Column(
        db.Integer, db.ForeignKey("knowledge_backpack.id"), nullable=False
    )
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    entry_type = db.Column(
        db.String(50), default="reflection"
    )  # reflection, goal, achievement
    tags = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    backpack = db.relationship("KnowledgeBackpack", backref="entries")


class BackpackAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    backpack_id = db.Column(
        db.Integer, db.ForeignKey("knowledge_backpack.id"), nullable=False
    )
    achievement_type = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(100), default="bi-trophy")
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)

    backpack = db.relationship("KnowledgeBackpack", backref="achievements")
