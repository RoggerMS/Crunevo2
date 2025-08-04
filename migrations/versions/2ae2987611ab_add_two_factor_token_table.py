"""add two_factor_token table

Revision ID: 2ae2987611ab
Revises: 9b7a1e2f4c8d
Create Date: 2025-07-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


def has_table(name: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


revision = "2ae2987611ab"
down_revision = "9b7a1e2f4c8d"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    if not has_table("two_factor_token", conn):
        op.create_table(
            "two_factor_token",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
            ),
            sa.Column("secret", sa.String(length=32), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("confirmed_at", sa.DateTime(), nullable=True),
            sa.Column("backup_codes", sa.Text(), nullable=True),
            if_not_exists=True,
        )


def downgrade():
    op.drop_table("two_factor_token", if_exists=True)
