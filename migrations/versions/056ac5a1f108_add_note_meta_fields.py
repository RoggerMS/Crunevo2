"""add note meta fields

Revision ID: 056ac5a1f108
Revises: 8f4f51464309
Create Date: 2025-06-26 00:45:49.193265

"""

from alembic import op
import sqlalchemy as sa


def has_col(table: str, column: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return any(c["name"] == column for c in inspector.get_columns(table))


# revision identifiers, used by Alembic.
revision = "056ac5a1f108"
down_revision = "8f4f51464309"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    with op.batch_alter_table("note", schema=None) as batch_op:
        if not has_col("note", "language", conn):
            batch_op.add_column(
                sa.Column("language", sa.String(length=20), nullable=True)
            )
        if not has_col("note", "reading_time", conn):
            batch_op.add_column(sa.Column("reading_time", sa.Integer(), nullable=True))
        if not has_col("note", "content_type", conn):
            batch_op.add_column(
                sa.Column("content_type", sa.String(length=20), nullable=True)
            )
        if not has_col("note", "summary", conn):
            batch_op.add_column(sa.Column("summary", sa.Text(), nullable=True))
        if not has_col("note", "course", conn):
            batch_op.add_column(
                sa.Column("course", sa.String(length=140), nullable=True)
            )
        if not has_col("note", "career", conn):
            batch_op.add_column(
                sa.Column("career", sa.String(length=140), nullable=True)
            )


def downgrade():
    with op.batch_alter_table("note", schema=None) as batch_op:
        batch_op.drop_column("career", if_exists=True)
        batch_op.drop_column("course", if_exists=True)
        batch_op.drop_column("summary", if_exists=True)
        batch_op.drop_column("content_type", if_exists=True)
        batch_op.drop_column("reading_time", if_exists=True)
        batch_op.drop_column("language", if_exists=True)
