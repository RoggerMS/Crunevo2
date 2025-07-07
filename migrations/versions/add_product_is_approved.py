"""add is_approved flag to product

Revision ID: add_product_is_approved
Revises: e8fb5094eccf
Create Date: 2025-08-30 00:00:00
"""

from alembic import op
import sqlalchemy as sa


def has_col(table: str, column: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return any(c["name"] == column for c in inspector.get_columns(table))

revision = "add_product_is_approved"
down_revision = "add_product_request"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    with op.batch_alter_table("product") as batch_op:
        if not has_col("product", "is_approved", conn):
            batch_op.add_column(
                sa.Column(
                    "is_approved",
                    sa.Boolean(),
                    nullable=True,
                    server_default=sa.true(),
                )
            )


def downgrade():
    with op.batch_alter_table("product") as batch_op:
        batch_op.drop_column("is_approved", if_exists=True)
