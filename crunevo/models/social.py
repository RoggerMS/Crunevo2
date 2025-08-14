from datetime import datetime
from crunevo.extensions import db
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import relationship
import enum


class MentorshipStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CompetitionStatus(enum.Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ChallengeType(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ChallengeStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"


class Mentorship(db.Model):
    __tablename__ = "mentorships"

    id = Column(Integer, primary_key=True)
    mentor_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    subject_area = Column(String(100), nullable=False)
    message = Column(Text)
    status = Column(Enum(MentorshipStatus), default=MentorshipStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Relationships
    mentor = relationship(
        "User", foreign_keys=[mentor_id], backref="mentoring_sessions"
    )
    student = relationship(
        "User", foreign_keys=[student_id], backref="learning_sessions"
    )


class StudyGroup(db.Model):
    __tablename__ = "study_groups"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    subject = Column(String(50), nullable=False)
    max_members = Column(Integer, default=10)
    creator_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    creator = relationship("User", backref="created_study_groups")
    members = relationship("StudyGroupMember", back_populates="group")


class StudyGroupMember(db.Model):
    __tablename__ = "study_group_members"

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("study_groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    group = relationship("StudyGroup", back_populates="members")
    user = relationship("User", backref="study_group_memberships")


class Competition(db.Model):
    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    subject = Column(String(50), nullable=False)
    difficulty = Column(String(20), nullable=False)  # beginner, intermediate, advanced
    prize_crolars = Column(Integer, default=0)
    entry_fee = Column(Integer, default=0)
    max_participants = Column(Integer)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(Enum(CompetitionStatus), default=CompetitionStatus.UPCOMING)
    creator_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    creator = relationship("User", backref="created_competitions")
    participants = relationship("CompetitionParticipant", back_populates="competition")


class CompetitionParticipant(db.Model):
    __tablename__ = "competition_participants"

    id = Column(Integer, primary_key=True)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    score = Column(Integer, default=0)
    rank = Column(Integer)

    # Relationships
    competition = relationship("Competition", back_populates="participants")
    user = relationship("User", backref="competition_participations")


class Challenge(db.Model):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    challenge_type = Column(Enum(ChallengeType), nullable=False)
    reward_crolars = Column(Integer, default=0)
    target_value = Column(Integer, nullable=False)  # e.g., 5 questions, 3 answers
    target_action = Column(
        String(50), nullable=False
    )  # e.g., 'ask_questions', 'answer_questions'
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user_challenges = relationship("UserChallenge", back_populates="challenge")


class UserChallenge(db.Model):
    __tablename__ = "user_challenges"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    progress = Column(Integer, default=0)
    status = Column(Enum(ChallengeStatus), default=ChallengeStatus.ACTIVE)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    reward_claimed = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", backref="user_challenges")
    challenge = relationship("Challenge", back_populates="user_challenges")
