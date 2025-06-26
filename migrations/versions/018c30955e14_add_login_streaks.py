"""add login streaks table

Revision ID: 018c30955e14
Revises: 81c3610645b1
Create Date: 2025-07-05 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "018c30955e14"
down_revision = "81c3610645b1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "login_streak",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), primary_key=True),
        sa.Column("current_day", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_login", sa.Date(), nullable=True),
        sa.Column("streak_start", sa.Date(), nullable=True),
    )


def downgrade():
    op.drop_table("login_streak")
