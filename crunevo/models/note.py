from datetime import datetime
from crunevo.extensions import db


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, default="")
    filename = db.Column(db.String(200), default="")
    original_file_url = db.Column(db.String(200), default="")
    file_type = db.Column(db.String(20), default="")
    tags = db.Column(db.String(200), default="")
    category = db.Column(db.String(100), default="")
    language = db.Column(db.String(20), default="")
    reading_time = db.Column(db.Integer)
    content_type = db.Column(db.String(20), default="")
    summary = db.Column(db.Text, default="")
    course = db.Column(db.String(140), default="")
    career = db.Column(db.String(140), default="")
    views = db.Column(db.Integer, default=0)
    downloads = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    comments = db.relationship("Comment", backref="note", lazy=True)

    @property
    def rating(self):
        """Optional rating attribute for backward compatibility.

        Notes historically exposed a ``rating`` field that no longer exists in
        the database. Some views or templates may still attempt to access this
        attribute, so we provide a lightweight property that returns any value
        assigned at runtime or ``None`` when unavailable.
        """

        return getattr(self, "_rating", None)

    @rating.setter
    def rating(self, value):
        self._rating = value
