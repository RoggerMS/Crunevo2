"""add saved post

Revision ID: 2fca2c9996c5
Revises: a1b2c3d4e5f6
Create Date: 2025-06-22 10:12:46.504648
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "2fca2c9996c5"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "saved_post",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("posts.id"), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        if_not_exists=True,
    )


def downgrade():
    op.drop_table("saved_post", if_exists=True)
