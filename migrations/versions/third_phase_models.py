
"""Add third phase models: certificates, club posts, event participation, saved content

Revision ID: third_phase_2024
Revises: new_sections_2024
Create Date: 2024-01-15 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = 'third_phase_2024'
down_revision = 'new_sections_2024'
branch_labels = None
depends_on = None


def upgrade():
    # Create certificate table
    op.create_table('certificate',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('certificate_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('issued_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create club_post table
    op.create_table('club_post',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('club_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('likes', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['club_id'], ['club.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create event_participation table
    op.create_table('event_participation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.Column('attended', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['event.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create saved_content table
    op.create_table('saved_content',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.String(length=20), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('saved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'content_type', 'content_id')
    )


def downgrade():
    op.drop_table('saved_content')
    op.drop_table('event_participation')
    op.drop_table('club_post')
    op.drop_table('certificate')
