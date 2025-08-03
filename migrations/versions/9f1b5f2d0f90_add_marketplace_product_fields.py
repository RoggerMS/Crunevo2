"""Add marketplace fields and tables"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "9f1b5f2d0f90"
down_revision = "forum_modernization_schema"
branch_labels = None
depends_on = None


def has_table(name: str, conn) -> bool:
    inspector = inspect(conn)
    return name in inspector.get_table_names()


def has_col(table: str, column: str, conn) -> bool:
    inspector = inspect(conn)
    return any(c["name"] == column for c in inspector.get_columns(table))


def upgrade():
    conn = op.get_bind()

    if not has_table("seller", conn):
        op.create_table(
            "seller",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False
            ),
            sa.Column("store_name", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text()),
            sa.Column("logo", sa.String(length=200)),
            sa.Column("banner", sa.String(length=200)),
            sa.Column("contact_email", sa.String(length=100)),
            sa.Column("contact_phone", sa.String(length=20)),
            sa.Column("address", sa.String(length=255)),
            sa.Column("rating", sa.Float(), server_default="0"),
            sa.Column("total_ratings", sa.Integer(), server_default="0"),
            sa.Column("total_sales", sa.Integer(), server_default="0"),
            sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
            if_not_exists=True,
        )

    if not has_table("marketplace_conversations", conn):
        op.create_table(
            "marketplace_conversations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "user1_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False
            ),
            sa.Column(
                "user2_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False
            ),
            sa.Column("product_id", sa.Integer()),
            sa.Column(
                "last_message_at", sa.DateTime(), server_default=sa.text("now()")
            ),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
            if_not_exists=True,
        )

    if not has_table("marketplace_messages", conn):
        op.create_table(
            "marketplace_messages",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "conversation_id",
                sa.Integer(),
                sa.ForeignKey("marketplace_conversations.id"),
                nullable=False,
            ),
            sa.Column(
                "sender_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False
            ),
            sa.Column(
                "receiver_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False
            ),
            sa.Column("product_id", sa.Integer()),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("is_read", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
            if_not_exists=True,
        )

    with op.batch_alter_table("product") as batch_op:
        if not has_col("product", "category", conn):
            batch_op.add_column(sa.Column("category", sa.String(length=50)))
        if not has_col("product", "subcategory", conn):
            batch_op.add_column(sa.Column("subcategory", sa.String(length=50)))
        if not has_col("product", "download_url", conn):
            batch_op.add_column(sa.Column("download_url", sa.String(length=255)))
        if not has_col("product", "seller_id", conn):
            batch_op.add_column(
                sa.Column("seller_id", sa.Integer(), sa.ForeignKey("seller.id"))
            )
        if not has_col("product", "condition", conn):
            batch_op.add_column(
                sa.Column("condition", sa.String(length=20), server_default="new")
            )
        if not has_col("product", "shipping_cost", conn):
            batch_op.add_column(
                sa.Column("shipping_cost", sa.Numeric(10, 2), server_default="0")
            )
        if not has_col("product", "shipping_time", conn):
            batch_op.add_column(sa.Column("shipping_time", sa.String(length=50)))
        if not has_col("product", "warranty", conn):
            batch_op.add_column(sa.Column("warranty", sa.String(length=100)))
        if not has_col("product", "tags", conn):
            batch_op.add_column(sa.Column("tags", sa.JSON()))
        if not has_col("product", "views_count", conn):
            batch_op.add_column(
                sa.Column("views_count", sa.Integer(), server_default="0")
            )
        if not has_col("product", "created_at", conn):
            batch_op.add_column(
                sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"))
            )
        if not has_col("product", "updated_at", conn):
            batch_op.add_column(
                sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"))
            )


def downgrade():
    with op.batch_alter_table("product") as batch_op:
        batch_op.drop_column("updated_at", if_exists=True)
        batch_op.drop_column("created_at", if_exists=True)
        batch_op.drop_column("views_count", if_exists=True)
        batch_op.drop_column("tags", if_exists=True)
        batch_op.drop_column("warranty", if_exists=True)
        batch_op.drop_column("shipping_time", if_exists=True)
        batch_op.drop_column("shipping_cost", if_exists=True)
        batch_op.drop_column("condition", if_exists=True)
        batch_op.drop_column("seller_id", if_exists=True)
        batch_op.drop_column("download_url", if_exists=True)
        batch_op.drop_column("subcategory", if_exists=True)
        batch_op.drop_column("category", if_exists=True)

    op.drop_table("marketplace_messages", if_exists=True)
    op.drop_table("marketplace_conversations", if_exists=True)
    op.drop_table("seller", if_exists=True)
