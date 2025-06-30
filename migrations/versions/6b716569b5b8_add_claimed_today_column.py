"""add claimed_today column to login_streak

Revision ID: 6b716569b5b8
Revises: 018c30955e14
Create Date: 2025-07-06 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


def has_col(table: str, column: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return any(c["name"] == column for c in inspector.get_columns(table))


# revision identifiers, used by Alembic.
revision = "6b716569b5b8"
down_revision = "018c30955e14"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    if not has_col("login_streak", "claimed_today", conn):
        op.add_column(
            "login_streak",
            sa.Column("claimed_today", sa.Date(), nullable=True),
            schema=None,
            if_not_exists=True,
        )


def downgrade():
    op.drop_column("login_streak", "claimed_today", if_exists=True)
