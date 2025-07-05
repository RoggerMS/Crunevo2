from crunevo.extensions import db


class UserBlock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blocker_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    blocked_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    __table_args__ = (
        db.UniqueConstraint("blocker_id", "blocked_id", name="uniq_user_block"),
    )

    blocker = db.relationship("User", foreign_keys=[blocker_id])
    blocked = db.relationship("User", foreign_keys=[blocked_id])
