"""add note_votes table

Revision ID: f47bb65af23c
Revises: ee8b2f2a9f0c
Create Date: 2025-06-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f47bb65af23c'
down_revision = 'ee8b2f2a9f0c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'note_vote',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('note_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.ForeignKeyConstraint(['note_id'], ['note.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'note_id', name='unique_vote')
    )


def downgrade():
    op.drop_table('note_vote')

