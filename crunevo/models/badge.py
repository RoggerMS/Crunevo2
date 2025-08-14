from crunevo.extensions import db
from datetime import datetime


class ForumBadge(db.Model):
    """Model for forum badges/achievements."""

    __tablename__ = "forum_badges"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(100), nullable=False)  # Icon class or URL
    category = db.Column(
        db.String(50), nullable=False
    )  # participation, quality, expertise, special
    rarity = db.Column(db.String(20), default="common")  # common, rare, epic, legendary
    points_reward = db.Column(db.Integer, default=0)
    requirements = db.Column(db.JSON)  # JSON with requirements
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with user badges
    user_badges = db.relationship("UserBadge", back_populates="badge", lazy="dynamic")

    def __repr__(self):
        return f"<ForumBadge {self.name}>"

    @staticmethod
    def get_default_badges():
        """Get list of default badges to create."""
        return [
            {
                "name": "Primera Pregunta",
                "description": "Hiciste tu primera pregunta en el foro",
                "icon": "fas fa-question-circle",
                "category": "participation",
                "rarity": "common",
                "points_reward": 10,
                "requirements": {"questions_asked": 1},
            },
            {
                "name": "Primera Respuesta",
                "description": "Diste tu primera respuesta en el foro",
                "icon": "fas fa-reply",
                "category": "participation",
                "rarity": "common",
                "points_reward": 15,
                "requirements": {"answers_given": 1},
            },
            {
                "name": "Preguntón",
                "description": "Hiciste 10 preguntas",
                "icon": "fas fa-question",
                "category": "participation",
                "rarity": "common",
                "points_reward": 50,
                "requirements": {"questions_asked": 10},
            },
            {
                "name": "Colaborador",
                "description": "Diste 25 respuestas",
                "icon": "fas fa-hands-helping",
                "category": "participation",
                "rarity": "rare",
                "points_reward": 100,
                "requirements": {"answers_given": 25},
            },
            {
                "name": "Mejor Respuesta",
                "description": "Tu respuesta fue marcada como la mejor",
                "icon": "fas fa-star",
                "category": "quality",
                "rarity": "rare",
                "points_reward": 25,
                "requirements": {"best_answers": 1},
            },
            {
                "name": "Experto",
                "description": "Tienes 10 mejores respuestas",
                "icon": "fas fa-medal",
                "category": "quality",
                "rarity": "epic",
                "points_reward": 200,
                "requirements": {"best_answers": 10},
            },
            {
                "name": "Útil",
                "description": "Recibiste 50 votos positivos",
                "icon": "fas fa-thumbs-up",
                "category": "quality",
                "rarity": "rare",
                "points_reward": 75,
                "requirements": {"helpful_votes": 50},
            },
            {
                "name": "Racha de 7 días",
                "description": "Participaste 7 días consecutivos",
                "icon": "fas fa-fire",
                "category": "participation",
                "rarity": "rare",
                "points_reward": 100,
                "requirements": {"forum_streak": 7},
            },
            {
                "name": "Mentor",
                "description": "Alcanzaste el nivel 7 en el foro",
                "icon": "fas fa-graduation-cap",
                "category": "expertise",
                "rarity": "epic",
                "points_reward": 300,
                "requirements": {"forum_level": 7},
            },
            {
                "name": "Leyenda",
                "description": "Alcanzaste el nivel máximo del foro",
                "icon": "fas fa-crown",
                "category": "expertise",
                "rarity": "legendary",
                "points_reward": 500,
                "requirements": {"forum_level": 10},
            },
        ]


class UserBadge(db.Model):
    """Model for user-badge relationships."""

    __tablename__ = "user_badges"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey("forum_badges.id"), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_displayed = db.Column(db.Boolean, default=True)  # Whether to show on profile

    # Relationships
    user = db.relationship("User", backref="user_badges")
    badge = db.relationship("ForumBadge", back_populates="user_badges")

    # Unique constraint to prevent duplicate badges
    __table_args__ = (
        db.UniqueConstraint("user_id", "badge_id", name="unique_user_badge"),
    )

    def __repr__(self):
        return f"<UserBadge {self.user_id}-{self.badge_id}>"
