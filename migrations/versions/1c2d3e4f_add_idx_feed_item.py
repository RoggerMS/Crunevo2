"""add composite index to feed_item

Revision ID: 1c2d3e4f
Revises: 0fd2f1e9be5a
Create Date: 2025-06-12 10:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "1c2d3e4f"
down_revision = "0fd2f1e9be5a"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "idx_feed_owner_score",
        "feed_item",
        ["owner_id", sa.text("score DESC"), sa.text("created_at DESC")],
    )


def downgrade():
    op.drop_index("idx_feed_owner_score", table_name="feed_item")
