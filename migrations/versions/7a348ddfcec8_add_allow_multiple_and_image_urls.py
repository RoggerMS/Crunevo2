"""add allow_multiple and image_urls

Revision ID: 7a348ddfcec8
Revises: 1a80ed700a38
Create Date: 2025-06-22 08:11:22.024329

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7a348ddfcec8"
down_revision = "1a80ed700a38"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("product")}
    if "allow_multiple" not in cols:
        op.add_column(
            "product",
            sa.Column(
                "allow_multiple",
                sa.Boolean(),
                server_default=sa.true(),
                nullable=True,
            ),
        )
    if "image_urls" not in cols:
        op.add_column("product", sa.Column("image_urls", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("product", "image_urls", if_exists=True)
    op.drop_column("product", "allow_multiple", if_exists=True)
