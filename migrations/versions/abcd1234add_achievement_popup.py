"""add achievement popup table and credit reward

Revision ID: abcd1234add
Revises: 20c9b1f4eabc
Create Date: 2025-07-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "abcd1234add"
down_revision = "20c9b1f4eabc"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("achievement") as batch_op:
        batch_op.add_column(
            sa.Column("credit_reward", sa.Integer(), nullable=True, server_default="1")
        )
    op.create_table(
        "achievement_popup",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column(
            "achievement_id",
            sa.Integer(),
            sa.ForeignKey("achievement.id"),
            nullable=False,
        ),
        sa.Column(
            "shown",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade():
    op.drop_table("achievement_popup")
    with op.batch_alter_table("achievement") as batch_op:
        batch_op.drop_column("credit_reward")
