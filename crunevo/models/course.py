
from datetime import datetime
from crunevo.extensions import db


class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    youtube_url = db.Column(db.String(500), nullable=False)
    thumbnail_url = db.Column(db.String(500))
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(100))
    duration_minutes = db.Column(db.Integer)
    difficulty = db.Column(db.String(20), default='Básico')  # Básico, Intermedio, Avanzado
    is_featured = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='created_courses')
    saved_by = db.relationship('SavedCourse', back_populates='course', cascade='all, delete-orphan')
    
    @property
    def youtube_embed_url(self):
        """Convert YouTube URL to embed format"""
        if 'youtube.com/watch?v=' in self.youtube_url:
            video_id = self.youtube_url.split('watch?v=')[1].split('&')[0]
            return f"https://www.youtube.com/embed/{video_id}"
        elif 'youtu.be/' in self.youtube_url:
            video_id = self.youtube_url.split('youtu.be/')[1].split('?')[0]
            return f"https://www.youtube.com/embed/{video_id}"
        return self.youtube_url


class SavedCourse(db.Model):
    __tablename__ = 'saved_courses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='saved_courses')
    course = db.relationship('Course', back_populates='saved_by')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'course_id', name='_user_course_uc'),)
