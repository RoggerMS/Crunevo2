"""add comments_count to note

Revision ID: b4636fc14d35
Revises: 1c2d3e4f
Create Date: 2025-07-01 00:00:00

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b4636fc14d35"
down_revision = "1c2d3e4f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "note",
        sa.Column("comments_count", sa.Integer(), nullable=True, server_default="0"),
    )
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE note SET comments_count = 0"))
    if conn.dialect.name != "sqlite":
        op.alter_column("note", "comments_count", server_default=None)


def downgrade():
    op.drop_column("note", "comments_count")
