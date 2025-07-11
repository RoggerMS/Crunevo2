"""add original_file_url to note

Revision ID: add_note_original_url
Revises: add_product_is_approved
Create Date: 2025-09-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


def has_col(table: str, column: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return any(c["name"] == column for c in inspector.get_columns(table))


revision = "add_note_original_url"
down_revision = "add_product_is_approved"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    with op.batch_alter_table("note", schema=None) as batch_op:
        if not has_col("note", "original_file_url", conn):
            batch_op.add_column(
                sa.Column("original_file_url", sa.String(length=200), nullable=True)
            )


def downgrade():
    with op.batch_alter_table("note", schema=None) as batch_op:
        batch_op.drop_column("original_file_url", if_exists=True)
