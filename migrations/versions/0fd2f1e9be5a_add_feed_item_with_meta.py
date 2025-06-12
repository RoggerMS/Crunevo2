"""add feed item with metadata

Revision ID: 0fd2f1e9be5a
Revises: f47bb65af23c
Create Date: 2025-06-12 05:45:00.000000

"""

from alembic import op
import sqlalchemy as sa

revision = "0fd2f1e9be5a"
down_revision = "f47bb65af23c"
branch_labels = None
depends_on = None

item_enum = sa.Enum(
    "apunte",
    "post",
    "logro",
    "movimiento",
    "evento",
    "mensaje",
    name="feed_item_type",
)


def upgrade():
    item_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "feed_item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("item_type", item_enum, nullable=False),
        sa.Column("ref_id", sa.Integer(), nullable=False),
        sa.Column("is_highlight", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("metadata", sa.Text()),
        sa.Column("score", sa.Float(), server_default="0"),
        sa.Column("created_at", sa.DateTime()),
    )


def downgrade():
    op.drop_table("feed_item")
    item_enum.drop(op.get_bind(), checkfirst=True)
