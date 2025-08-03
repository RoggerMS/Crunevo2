"""add_product_is_official

Revision ID: add_product_is_official
Revises: 9f1b5f2d0f90
Create Date: 2025-08-03 19:29:48.227932

"""

from alembic import op
import sqlalchemy as sa


def has_col(table: str, column: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return any(c["name"] == column for c in inspector.get_columns(table))


# revision identifiers, used by Alembic.
revision = "add_product_is_official"
down_revision = "9f1b5f2d0f90"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    with op.batch_alter_table("product") as batch_op:
        if not has_col("product", "is_official", conn):
            batch_op.add_column(
                sa.Column(
                    "is_official",
                    sa.Boolean(),
                    nullable=True,
                    server_default=sa.false(),
                )
            )


def downgrade():
    with op.batch_alter_table("product") as batch_op:
        batch_op.drop_column("is_official", if_exists=True)
