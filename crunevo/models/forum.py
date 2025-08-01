from datetime import datetime
from crunevo.extensions import db


# Association table for question tags
question_tags = db.Table('question_tags',
    db.Column('question_id', db.Integer, db.ForeignKey('forum_question.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('forum_tag.id'), primary_key=True)
)

# Association table for user question bookmarks
user_bookmarks = db.Table('user_bookmarks',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('question_id', db.Integer, db.ForeignKey('forum_question.id'), primary_key=True)
)

# Association table for answer votes
answer_votes = db.Table('answer_votes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('answer_id', db.Integer, db.ForeignKey('forum_answer.id'), primary_key=True),
    db.Column('vote_type', db.String(10), nullable=False)  # 'up' or 'down'
)


class ForumTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    color = db.Column(db.String(7), default='#667eea')  # Hex color
    icon = db.Column(db.String(50), default='bi-tag')  # Bootstrap icon class
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def question_count(self):
        return ForumQuestion.query.filter(ForumQuestion.tags.contains(self)).count()


class ForumQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    difficulty_level = db.Column(db.String(20), default='intermedio')  # basico, intermedio, avanzado
    subject_area = db.Column(db.String(100))  # More specific than category
    grade_level = db.Column(db.String(20))  # e.g., "6to-primaria", "1ro-secundaria"
    bounty_points = db.Column(db.Integer, default=0)  # Points offered for best answer
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    views = db.Column(db.Integer, default=0)
    is_solved = db.Column(db.Boolean, default=False)
    is_urgent = db.Column(db.Boolean, default=False)  # For urgent homework help
    is_featured = db.Column(db.Boolean, default=False)  # Featured questions
    quality_score = db.Column(db.Float, default=0.0)  # Auto-calculated quality score
    
    # New: Study context
    homework_deadline = db.Column(db.DateTime)  # When homework is due
    exam_date = db.Column(db.DateTime)  # If preparing for exam
    context_type = db.Column(db.String(50), default='general')  # homework, exam, curiosity, project

    # Relationships
    author = db.relationship("User", backref="forum_questions")
    answers = db.relationship(
        "ForumAnswer", backref="question", lazy=True, cascade="all, delete-orphan"
    )
    tags = db.relationship('ForumTag', secondary=question_tags, lazy='subquery',
                          backref=db.backref('questions', lazy=True))
    bookmarked_by = db.relationship('User', secondary=user_bookmarks, lazy='subquery',
                                   backref=db.backref('bookmarked_questions', lazy=True))

    @property
    def answer_count(self):
        return len(self.answers)
    
    @property
    def helpful_answer_count(self):
        return len([a for a in self.answers if a.votes > 0])
    
    @property
    def average_answer_quality(self):
        if not self.answers:
            return 0
        return sum(max(0, a.votes) for a in self.answers) / len(self.answers)
    
    @property
    def urgency_score(self):
        """Calculate urgency based on deadline and other factors"""
        score = 0
        if self.is_urgent:
            score += 50
        if self.homework_deadline:
            days_left = (self.homework_deadline - datetime.utcnow()).days
            if days_left <= 1:
                score += 40
            elif days_left <= 3:
                score += 20
        if not self.is_solved and self.bounty_points > 0:
            score += min(30, self.bounty_points // 10)
        return min(100, score)


class ForumAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    explanation_quality = db.Column(db.String(20), default='good')  # poor, good, excellent
    has_step_by_step = db.Column(db.Boolean, default=False)  # Auto-detected or manually set
    has_visual_aids = db.Column(db.Boolean, default=False)  # Images, diagrams
    is_expert_verified = db.Column(db.Boolean, default=False)  # Verified by expert
    confidence_level = db.Column(db.String(20), default='medium')  # low, medium, high
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
    helpful_count = db.Column(db.Integer, default=0)  # Separate "helpful" votes
    
    # New: Answer analysis
    word_count = db.Column(db.Integer, default=0)
    estimated_reading_time = db.Column(db.Integer, default=1)  # minutes
    contains_formulas = db.Column(db.Boolean, default=False)
    contains_code = db.Column(db.Boolean, default=False)

    # Relationships
    author = db.relationship("User", backref="forum_answers")
    voters = db.relationship('User', secondary=answer_votes, lazy='subquery',
                           backref=db.backref('voted_answers', lazy=True))
    
    @property
    def quality_score(self):
        """Calculate answer quality based on multiple factors"""
        score = 0
        
        # Base score from votes
        score += max(0, self.votes) * 10
        
        # Bonus for accepted answers
        if self.is_accepted:
            score += 50
            
        # Bonus for step-by-step explanations
        if self.has_step_by_step:
            score += 20
            
        # Bonus for visual aids
        if self.has_visual_aids:
            score += 15
            
        # Bonus for expert verification
        if self.is_expert_verified:
            score += 30
            
        # Length bonus (not too short, not too long)
        if 100 <= self.word_count <= 500:
            score += 10
        elif self.word_count > 500:
            score += 5
            
        return min(100, score)


class ForumReport(db.Model):
    """For community moderation"""
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    reported_question_id = db.Column(db.Integer, db.ForeignKey("forum_question.id"))
    reported_answer_id = db.Column(db.Integer, db.ForeignKey("forum_answer.id"))
    reason = db.Column(db.String(100), nullable=False)  # spam, inappropriate, off-topic, etc.
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reporter = db.relationship("User", backref="reports_made")
    question = db.relationship("ForumQuestion", backref="reports")
    answer = db.relationship("ForumAnswer", backref="reports")


class ForumBadge(db.Model):
    """Gamification badges for users"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    icon = db.Column(db.String(50), default='bi-award')
    color = db.Column(db.String(7), default='#ffd700')
    category = db.Column(db.String(50))  # helper, solver, contributor, etc.
    requirement_type = db.Column(db.String(50))  # answers_count, votes_received, etc.
    requirement_value = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# Association table for user badges
user_badges = db.Table('user_badges',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('badge_id', db.Integer, db.ForeignKey('forum_badge.id'), primary_key=True),
    db.Column('earned_at', db.DateTime, default=datetime.utcnow)
)
