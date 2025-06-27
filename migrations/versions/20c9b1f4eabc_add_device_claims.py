"""add device claims table

Revision ID: 20c9b1f4eabc
Revises: 123456789abc
Create Date: 2025-09-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "20c9b1f4eabc"
down_revision = "123456789abc"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "device_claim",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("device_token", sa.String(length=255), nullable=False, index=True),
        sa.Column("mission_code", sa.String(length=50), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table("device_claim")
