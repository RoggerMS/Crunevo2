"""Add forum gamification fields to user table

Revision ID: bfe408324362
Revises: 5007130f0224
Create Date: 2025-08-13 13:32:23.294429

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bfe408324362'
down_revision = '5007130f0224'
branch_labels = None
depends_on = None


def upgrade():
    # Add forum gamification fields to user table
    op.add_column('user', sa.Column('forum_level', sa.Integer(), nullable=True, default=1))
    op.add_column('user', sa.Column('forum_experience', sa.Integer(), nullable=True, default=0))
    op.add_column('user', sa.Column('forum_streak', sa.Integer(), nullable=True, default=0))
    op.add_column('user', sa.Column('last_activity_date', sa.Date(), nullable=True))
    op.add_column('user', sa.Column('questions_asked', sa.Integer(), nullable=True, default=0))
    op.add_column('user', sa.Column('answers_given', sa.Integer(), nullable=True, default=0))
    op.add_column('user', sa.Column('best_answers', sa.Integer(), nullable=True, default=0))
    op.add_column('user', sa.Column('helpful_votes', sa.Integer(), nullable=True, default=0))
    op.add_column('user', sa.Column('reputation_score', sa.Integer(), nullable=True, default=0))
    op.add_column('user', sa.Column('custom_forum_title', sa.String(length=50), nullable=True))
    
    # Set default values for existing users
    op.execute("UPDATE \"user\" SET forum_level = 1 WHERE forum_level IS NULL")
    op.execute("UPDATE \"user\" SET forum_experience = 0 WHERE forum_experience IS NULL")
    op.execute("UPDATE \"user\" SET forum_streak = 0 WHERE forum_streak IS NULL")
    op.execute("UPDATE \"user\" SET questions_asked = 0 WHERE questions_asked IS NULL")
    op.execute("UPDATE \"user\" SET answers_given = 0 WHERE answers_given IS NULL")
    op.execute("UPDATE \"user\" SET best_answers = 0 WHERE best_answers IS NULL")
    op.execute("UPDATE \"user\" SET helpful_votes = 0 WHERE helpful_votes IS NULL")
    op.execute("UPDATE \"user\" SET reputation_score = 0 WHERE reputation_score IS NULL")


def downgrade():
    # Remove forum gamification fields from user table
    op.drop_column('user', 'custom_forum_title')
    op.drop_column('user', 'reputation_score')
    op.drop_column('user', 'helpful_votes')
    op.drop_column('user', 'best_answers')
    op.drop_column('user', 'answers_given')
    op.drop_column('user', 'questions_asked')
    op.drop_column('user', 'last_activity_date')
    op.drop_column('user', 'forum_streak')
    op.drop_column('user', 'forum_experience')
    op.drop_column('user', 'forum_level')
