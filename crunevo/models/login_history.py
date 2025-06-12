from datetime import date
from crunevo.extensions import db


class LoginHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    login_date = db.Column(db.Date, default=date.today, nullable=False)

    user = db.relationship('User', backref='login_history')
