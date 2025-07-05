"""add page view table

Revision ID: add_page_view
Revises: 018c30955e14
Create Date: 2025-07-05 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


def has_table(name: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


revision = "add_page_view"
down_revision = "add_site_config"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    if not has_table("page_view", conn):
        op.create_table(
            "page_view",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("path", sa.String(length=300), nullable=False),
            sa.Column("timestamp", sa.DateTime(), nullable=True),
            if_not_exists=True,
        )


def downgrade():
    op.drop_table("page_view", if_exists=True)
