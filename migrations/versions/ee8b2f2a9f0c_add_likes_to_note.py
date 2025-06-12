"""add likes to note

Revision ID: ee8b2f2a9f0c
Revises: ad2c58317e3c
Create Date: 2025-06-12 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ee8b2f2a9f0c"
down_revision = "ad2c58317e3c"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "note", sa.Column("likes", sa.Integer(), nullable=True, server_default="0")
    )
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.alter_column("note", "likes", server_default=None)


def downgrade():
    op.drop_column("note", "likes")
