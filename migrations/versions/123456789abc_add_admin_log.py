"""add admin log table

Revision ID: 123456789abc
Revises: 6b716569b5b8
Create Date: 2025-08-01 00:00:00
"""

from alembic import op
import sqlalchemy as sa


def has_table(name: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


revision = "123456789abc"
down_revision = "6b716569b5b8"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    if not has_table("admin_log", conn):
        op.create_table(
            "admin_log",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "admin_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False
            ),
            sa.Column("action", sa.String(length=50), nullable=False),
            sa.Column("target_id", sa.Integer(), nullable=True),
            sa.Column("target_type", sa.String(length=30), nullable=True),
            sa.Column("timestamp", sa.DateTime(), nullable=True),
            if_not_exists=True,
        )


def downgrade():
    op.drop_table("admin_log", if_exists=True)
