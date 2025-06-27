from crunevo.extensions import db


class AchievementPopup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    achievement_id = db.Column(
        db.Integer, db.ForeignKey("achievement.id"), nullable=False
    )
    shown = db.Column(db.Boolean, default=False)

    user = db.relationship("User")
    achievement = db.relationship("Achievement")
