"""add claimed_today column to login_streak

Revision ID: 6b716569b5b8
Revises: 018c30955e14
Create Date: 2025-07-06 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "6b716569b5b8"
down_revision = "018c30955e14"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("login_streak", sa.Column("claimed_today", sa.Date(), nullable=True))


def downgrade():
    op.drop_column("login_streak", "claimed_today")
