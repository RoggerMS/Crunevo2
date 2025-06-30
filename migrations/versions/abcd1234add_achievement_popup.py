"""add achievement popup table and credit reward

Revision ID: abcd1234add
Revises: 20c9b1f4eabc
Create Date: 2025-07-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


def has_col(table: str, column: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return any(c["name"] == column for c in inspector.get_columns(table))


revision = "abcd1234add"
down_revision = "20c9b1f4eabc"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    with op.batch_alter_table("achievement") as batch_op:
        if not has_col("achievement", "credit_reward", conn):
            batch_op.add_column(
                sa.Column(
                    "credit_reward", sa.Integer(), nullable=True, server_default="1"
                )
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
        if_not_exists=True,
    )


def downgrade():
    op.drop_table("achievement_popup", if_exists=True)
    with op.batch_alter_table("achievement") as batch_op:
        batch_op.drop_column("credit_reward", if_exists=True)
