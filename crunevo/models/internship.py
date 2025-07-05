from datetime import datetime
from crunevo.extensions import db


class Internship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    field = db.Column(db.String(100))
    location = db.Column(db.String(100))
    company = db.Column(db.String(100))
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)


class InternshipApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    internship_id = db.Column(
        db.Integer, db.ForeignKey("internship.id"), nullable=False
    )
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    cover_letter = db.Column(db.Text)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

    internship = db.relationship("Internship", backref="applications")
    user = db.relationship("User", backref="internship_applications")
