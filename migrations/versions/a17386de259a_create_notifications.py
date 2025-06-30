"""create notifications

Revision ID: a17386de259a
Revises: 2fca2c9996c5
Create Date: 2025-06-22 22:01:27.724507

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a17386de259a"
down_revision = "2fca2c9996c5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("message", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=255), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        if_not_exists=True,
    )


def downgrade():
    op.drop_table("notifications", if_exists=True)
