"""add verification_level to user

Revision ID: f4c1c2d3e4f5
Revises: e3a1b7c4a9b1
Create Date: 2025-06-12 17:26:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "f4c1c2d3e4f5"
down_revision = "e3a1b7c4a9b1"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='user' AND column_name='verification_level'"
        )
    )
    exists = result.first() is not None

    if not exists:
        op.add_column(
            "user",
            sa.Column("verification_level", sa.SmallInteger(), nullable=False, server_default="0")
        )
        op.alter_column("user", "verification_level", server_default=None)



def downgrade():
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='user' AND column_name='verification_level'"
        )
    )
    exists = result.first() is not None

    if exists:
        op.drop_column("user", "verification_level")

