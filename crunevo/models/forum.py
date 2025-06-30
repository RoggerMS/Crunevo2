from datetime import datetime
from crunevo.extensions import db


class ForumQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    views = db.Column(db.Integer, default=0)
    is_solved = db.Column(db.Boolean, default=False)

    # Relationships
    author = db.relationship("User", backref="forum_questions")
    answers = db.relationship(
        "ForumAnswer", backref="question", lazy=True, cascade="all, delete-orphan"
    )

    @property
    def answer_count(self):
        return len(self.answers)


class ForumAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    question_id = db.Column(
        db.Integer, db.ForeignKey("forum_question.id"), nullable=False
    )
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_accepted = db.Column(db.Boolean, default=False)
    votes = db.Column(db.Integer, default=0)

    # Relationships
    author = db.relationship("User", backref="forum_answers")
