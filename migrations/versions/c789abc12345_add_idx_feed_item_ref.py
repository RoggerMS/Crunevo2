"""add index type+ref to feed_item

Revision ID: c789abc12345
Revises: b4636fc14d35
Create Date: 2025-07-01 01:00:00

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "c789abc12345"
down_revision = "b4636fc14d35"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "idx_feed_type_ref",
        "feed_item",
        ["item_type", "ref_id"],
    )


def downgrade():
    op.drop_index("idx_feed_type_ref", table_name="feed_item")
