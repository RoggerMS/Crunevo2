from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from crunevo.extensions import db, login_manager


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default="student")
    points = db.Column(db.Integer, default=0)
    credits = db.Column(db.Integer, default=0)
    chat_enabled = db.Column(db.Boolean, default=True)
    avatar_url = db.Column(db.String(255))
    about = db.Column(db.Text)
    credit_history = db.relationship("Credit", back_populates="user", lazy=True)
    notes = db.relationship("Note", backref="author", lazy=True)
    posts = db.relationship("Post", backref="author", lazy=True)
    comments = db.relationship("Comment", backref="author", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
