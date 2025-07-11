"""add note file_type column

Revision ID: bdd3abdf7084
Revises: 056ac5a1f108
Create Date: 2025-12-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


def has_col(table: str, column: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return any(c["name"] == column for c in inspector.get_columns(table))


revision = "bdd3abdf7084"
down_revision = "add_note_original_url"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    with op.batch_alter_table("note", schema=None) as batch_op:
        if not has_col("note", "file_type", conn):
            batch_op.add_column(
                sa.Column("file_type", sa.String(length=20), nullable=True)
            )


def downgrade():
    with op.batch_alter_table("note", schema=None) as batch_op:
        batch_op.drop_column("file_type", if_exists=True)
