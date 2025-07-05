"""add user activity table

Revision ID: add_user_activity
Revises: 20c9b1f4eabc
Create Date: 2025-10-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


def has_table(name: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


revision = "add_user_activity"
down_revision = "9e8b7a4cd123"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    if not has_table("user_activity", conn):
        op.create_table(
            "user_activity",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False
            ),
            sa.Column("action", sa.String(length=30), nullable=False),
            sa.Column("target_id", sa.Integer(), nullable=True),
            sa.Column("target_type", sa.String(length=30), nullable=True),
            sa.Column("timestamp", sa.DateTime(), nullable=True),
            if_not_exists=True,
        )


def downgrade():
    op.drop_table("user_activity", if_exists=True)
