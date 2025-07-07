from datetime import datetime
from crunevo.extensions import db


class AcademicDuel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    challenger_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    challenged_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    question = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    reward_crolars = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(
        db.String(20), default="pending"
    )  # pending, answered, validated, rejected
    answer = db.Column(db.Text)
    answered_at = db.Column(db.DateTime)
    validated_at = db.Column(db.DateTime)
    is_correct = db.Column(db.Boolean)

    # Relationships
    challenger = db.relationship(
        "User", foreign_keys=[challenger_id], backref="duels_created"
    )
    challenged = db.relationship(
        "User", foreign_keys=[challenged_id], backref="duels_received"
    )

    @property
    def is_pending(self):
        return self.status == "pending"

    @property
    def is_answered(self):
        return self.status in ["answered", "validated"]

    @property
    def winner(self):
        if self.status == "validated" and self.is_correct:
            return self.challenged
        return None
