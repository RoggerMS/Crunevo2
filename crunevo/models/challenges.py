
from datetime import datetime
from crunevo.extensions import db


class GhostMentorChallenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    challenge_content = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.Text)
    reward_crolars = db.Column(db.Integer, default=25)
    reward_badge = db.Column(db.String(100))
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    difficulty_level = db.Column(db.String(20), default='medium')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    responses = db.relationship('GhostMentorResponse', backref='challenge', lazy='dynamic')


class GhostMentorResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('ghost_mentor_challenge.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    response_content = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    points_earned = db.Column(db.Integer, default=0)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='ghost_responses')


class MasterQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text)
    category = db.Column(db.String(100), default='general')
    difficulty = db.Column(db.String(20), default='hard')
    reward_crolars = db.Column(db.Integer, default=50)
    badge_code = db.Column(db.String(50), default='daily_master')
    active_date = db.Column(db.Date, nullable=False)
    is_answered = db.Column(db.Boolean, default=False)
    winner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    answered_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    winner = db.relationship('User', backref='won_master_questions')
    attempts = db.relationship('MasterQuestionAttempt', backref='question', lazy='dynamic')


class MasterQuestionAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('master_question.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    answer_given = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='master_attempts')
