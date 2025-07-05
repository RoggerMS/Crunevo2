"""add purchase shipping fields"""

from alembic import op
import sqlalchemy as sa


def has_col(table: str, column: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return any(c["name"] == column for c in inspector.get_columns(table))


revision = "add_purchase_shipping_fields"
down_revision = ("add_group_mission", "user_block_attachment")
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    with op.batch_alter_table("purchase") as batch_op:
        if not has_col("purchase", "shipping_address", conn):
            batch_op.add_column(
                sa.Column("shipping_address", sa.String(length=255), nullable=True)
            )
        if not has_col("purchase", "shipping_message", conn):
            batch_op.add_column(sa.Column("shipping_message", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("purchase") as batch_op:
        batch_op.drop_column("shipping_message", if_exists=True)
        batch_op.drop_column("shipping_address", if_exists=True)
