from flask_login import UserMixin
from crunevo.security.passwords import generate_hash, verify_hash
from crunevo.extensions import db, login_manager
from sqlalchemy import func

from .note import Note

# Default avatar used when no image is uploaded
DEFAULT_AVATAR_URL = (
    "https://res.cloudinary.com/dnp9trhfx/image/upload/v1750458582/avatar_h8okpo.png"
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), default="student")
    points = db.Column(db.Integer, default=0)
    credits = db.Column(db.Integer, default=0)
    chat_enabled = db.Column(db.Boolean, default=True)
    activated = db.Column(db.Boolean, default=False)
    verification_level = db.Column(db.SmallInteger, default=0)
    avatar_url = db.Column(db.String(255), default=DEFAULT_AVATAR_URL)
    about = db.Column(db.Text)
    career = db.Column(db.String(120))
    interests = db.Column(db.Text)
    credit_history = db.relationship("Credit", back_populates="user", lazy=True)
    notes = db.relationship("Note", backref="author", lazy=True)
    posts = db.relationship(
        "Post", backref="author", lazy=True, foreign_keys="Post.author_id"
    )
    comments = db.relationship("Comment", backref="author", lazy=True)
    post_comments = db.relationship("PostComment", backref="author", lazy=True)
    notifications = db.relationship(
        "Notification", back_populates="user", lazy="dynamic"
    )

    def set_password(self, password):
        self.password_hash = generate_hash(password)

    def check_password(self, password):
        return verify_hash(self.password_hash, password)

    def is_friend(self, other_user):
        """Placeholder friendship check."""
        return False

    @property
    def notes_count(self) -> int:
        """Return the number of notes authored by the user without loading them."""
        return (
            db.session.query(func.count(Note.id)).filter_by(user_id=self.id).scalar()
            or 0
        )


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
