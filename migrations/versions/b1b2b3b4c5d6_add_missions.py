"""add missions tables

Revision ID: b1b2b3b4c5d6
Revises: a17386de259a
Create Date: 2025-07-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b1b2b3b4c5d6"
down_revision = "a17386de259a"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "mission",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("description", sa.String(length=200), nullable=False),
        sa.Column("goal", sa.Integer(), nullable=True),
        sa.Column("credit_reward", sa.Integer(), nullable=True),
        sa.Column("achievement_code", sa.String(length=50), nullable=True),
        if_not_exists=True,
    )
    op.create_table(
        "user_mission",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "mission_id", sa.Integer(), sa.ForeignKey("mission.id"), nullable=False
        ),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        if_not_exists=True,
    )


def downgrade():
    op.drop_table("user_mission", if_exists=True)
    op.drop_table("mission", if_exists=True)
