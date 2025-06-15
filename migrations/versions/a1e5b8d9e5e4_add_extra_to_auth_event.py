"""add extra column to auth_event

Revision ID: a1e5b8d9e5e4
Revises: f4c1c2d3e4f5
Create Date: 2025-06-12 18:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "a1e5b8d9e5e4"
down_revision = "f4c1c2d3e4f5"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='auth_event' AND column_name='extra'"
        )
    )
    exists = result.first() is not None

    if not exists:
        op.add_column("auth_event", sa.Column("extra", sa.Text()))


def downgrade():
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='auth_event' AND column_name='extra'"
        )
    )
    exists = result.first() is not None

    if exists:
        op.drop_column("auth_event", "extra")
