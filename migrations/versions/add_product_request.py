"""add product request table

Revision ID: add_product_request
Revises: add_career_module
Create Date: 2025-07-07 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


def has_table(name: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


revision = "add_product_request"
down_revision = "add_career_module"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    if not has_table("product_request", conn):
        op.create_table(
            "product_request",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False
            ),
            sa.Column("name", sa.String(length=140), nullable=False),
            sa.Column("category", sa.String(length=50), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("price_soles", sa.Numeric(10, 2), nullable=True),
            sa.Column("image_url", sa.String(length=255), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            if_not_exists=True,
        )


def downgrade():
    op.drop_table("product_request", if_exists=True)
