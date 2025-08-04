"""add career and interests fields to user

Revision ID: 4c29ad8b8c1a
Revises: 018c30955e14
Create Date: 2025-07-08 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


def has_col(table: str, column: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return any(c["name"] == column for c in inspector.get_columns(table))


# revision identifiers, used by Alembic.
revision = "4c29ad8b8c1a"
down_revision = "add_api_key"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    with op.batch_alter_table("users", schema=None) as batch_op:
        if not has_col("users", "career", conn):
            batch_op.add_column(
                sa.Column("career", sa.String(length=120), nullable=True)
            )
        if not has_col("users", "interests", conn):
            batch_op.add_column(sa.Column("interests", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("interests", if_exists=True)
        batch_op.drop_column("career", if_exists=True)
