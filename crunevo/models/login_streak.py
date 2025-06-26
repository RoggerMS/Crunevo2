from crunevo.extensions import db


class LoginStreak(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    current_day = db.Column(db.Integer, nullable=False, default=0)
    last_login = db.Column(db.Date)
    streak_start = db.Column(db.Date)
    claimed_today = db.Column(db.Date)

    user = db.relationship("User", backref=db.backref("login_streak", uselist=False))
