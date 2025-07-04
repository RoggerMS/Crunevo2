"""add verification_request table

Revision ID: 9e8b7a4cd123
Revises: add_post_images
Create Date: 2025-07-06 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


def has_table(name: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


# revision identifiers, used by Alembic.
revision = "9e8b7a4cd123"
down_revision = "add_post_images"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    if not has_table("verification_request", conn):
        op.create_table(
            "verification_request",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False
            ),
            sa.Column("info", sa.Text(), nullable=False),
            sa.Column(
                "status", sa.String(length=20), nullable=True, server_default="pending"
            ),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            if_not_exists=True,
        )


def downgrade():
    op.drop_table("verification_request", if_exists=True)
