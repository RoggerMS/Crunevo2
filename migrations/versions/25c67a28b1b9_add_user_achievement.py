"""add user achievement

Revision ID: 25c67a28b1b9
Revises: 6c3e9b51bb42
Create Date: 2025-06-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '25c67a28b1b9'
down_revision = '6c3e9b51bb42'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_achievement',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('badge_code', sa.String(length=50), nullable=False),
        sa.Column('earned_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'])
    )


def downgrade():
    op.drop_table('user_achievement')

