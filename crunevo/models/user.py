from flask_login import UserMixin
from crunevo.security.passwords import generate_hash, verify_hash
from crunevo.extensions import db, login_manager

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
    mostrar_tienda_perfil = db.Column(db.Boolean, default=False)
    
    # Forum gamification fields
    forum_level = db.Column(db.Integer, default=1)
    forum_experience = db.Column(db.Integer, default=0)
    forum_streak = db.Column(db.Integer, default=0)
    last_activity_date = db.Column(db.Date)
    questions_asked = db.Column(db.Integer, default=0)
    answers_given = db.Column(db.Integer, default=0)
    best_answers = db.Column(db.Integer, default=0)
    helpful_votes = db.Column(db.Integer, default=0)
    reputation_score = db.Column(db.Integer, default=0)
    custom_forum_title = db.Column(db.String(50))  # Premium custom title
    
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
    
    def calculate_forum_level(self):
        """Calculate forum level based on experience points."""
        if self.forum_experience < 100:
            return 1
        elif self.forum_experience < 300:
            return 2
        elif self.forum_experience < 600:
            return 3
        elif self.forum_experience < 1000:
            return 4
        elif self.forum_experience < 1500:
            return 5
        elif self.forum_experience < 2500:
            return 6
        elif self.forum_experience < 4000:
            return 7
        elif self.forum_experience < 6000:
            return 8
        elif self.forum_experience < 9000:
            return 9
        else:
            return 10
    
    def add_forum_experience(self, points):
        """Add experience points and update level."""
        self.forum_experience += points
        new_level = self.calculate_forum_level()
        if new_level > self.forum_level:
            self.forum_level = new_level
            return True  # Level up occurred
        return False
    
    def get_level_progress(self):
        """Get progress towards next level as percentage."""
        level_thresholds = [0, 100, 300, 600, 1000, 1500, 2500, 4000, 6000, 9000, float('inf')]
        current_threshold = level_thresholds[self.forum_level - 1]
        next_threshold = level_thresholds[self.forum_level]
        
        if next_threshold == float('inf'):
            return 100
        
        progress = ((self.forum_experience - current_threshold) / 
                   (next_threshold - current_threshold)) * 100
        return min(100, max(0, progress))
    
    def get_forum_rank(self):
        """Get forum rank based on level."""
        ranks = {
            1: "Novato",
            2: "Aprendiz",
            3: "Estudiante",
            4: "Colaborador",
            5: "Experto Junior",
            6: "Experto",
            7: "Mentor",
            8: "Sabio",
            9: "Maestro",
            10: "Leyenda"
        }
        return ranks.get(self.forum_level, "Novato")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
