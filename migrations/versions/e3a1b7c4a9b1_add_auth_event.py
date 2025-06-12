"""add auth event table

Revision ID: e3a1b7c4a9b1
Revises: 76b3ec100daa
Create Date: 2025-06-12 17:25:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "e3a1b7c4a9b1"
down_revision = "76b3ec100daa"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "auth_event",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id")),
        sa.Column("event_type", sa.String(length=20), nullable=False),
        sa.Column("ip", sa.String(length=45)),
        sa.Column("ua", sa.String(length=255)),
        sa.Column("timestamp", sa.DateTime(), nullable=False, default=sa.func.now()),
    )


def downgrade():
    op.drop_table("auth_event")
