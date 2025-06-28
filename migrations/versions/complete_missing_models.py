
"""Complete missing models and relationships

Revision ID: complete_missing_models
Revises: add_courses_system
Create Date: 2024-12-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'complete_missing_models'
down_revision = 'add_courses_system'
branch_labels = None
depends_on = None


def upgrade():
    # Add missing columns to users if they don't exist
    try:
        op.add_column('user', sa.Column('pref_dark', sa.Boolean(), default=False))
    except:
        pass
    
    try:
        op.add_column('user', sa.Column('bio', sa.Text()))
    except:
        pass
    
    try:
        op.add_column('user', sa.Column('career', sa.String(100)))
    except:
        pass
    
    try:
        op.add_column('user', sa.Column('interests', sa.Text()))
    except:
        pass
    
    # Add missing columns to products if they don't exist
    try:
        op.add_column('product', sa.Column('active', sa.Boolean(), default=True))
    except:
        pass
    
    try:
        op.add_column('product', sa.Column('popularity_score', sa.Integer(), default=0))
    except:
        pass
    
    # Ensure club_member table exists
    try:
        op.create_table('club_member',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('club_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(20), default='member'),
        sa.Column('joined_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['club_id'], ['club.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'club_id')
        )
    except:
        pass
    
    # Ensure saved_course table exists
    try:
        op.create_table('saved_course',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('saved_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'course_id')
        )
    except:
        pass


def downgrade():
    try:
        op.drop_table('saved_course')
    except:
        pass
    
    try:
        op.drop_table('club_member')
    except:
        pass
    
    try:
        op.drop_column('product', 'popularity_score')
    except:
        pass
    
    try:
        op.drop_column('product', 'active')
    except:
        pass
    
    try:
        op.drop_column('user', 'interests')
    except:
        pass
    
    try:
        op.drop_column('user', 'career')
    except:
        pass
    
    try:
        op.drop_column('user', 'bio')
    except:
        pass
    
    try:
        op.drop_column('user', 'pref_dark')
    except:
        pass
