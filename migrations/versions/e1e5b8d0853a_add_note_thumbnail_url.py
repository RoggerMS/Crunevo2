"""add thumbnail_url column to note

Revision ID: e1e5b8d0853a
Revises: 5683aa47fe36
Create Date: 2025-08-08 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


def has_col(table: str, column: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return any(c["name"] == column for c in inspector.get_columns(table))


# revision identifiers, used by Alembic.
revision = "e1e5b8d0853a"
down_revision = "5683aa47fe36"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    with op.batch_alter_table("note", schema=None) as batch_op:
        if not has_col("note", "thumbnail_url", conn):
            batch_op.add_column(
                sa.Column("thumbnail_url", sa.String(length=200), nullable=True, server_default="")
            )


def downgrade():
    with op.batch_alter_table("note", schema=None) as batch_op:
        batch_op.drop_column("thumbnail_url", if_exists=True)
