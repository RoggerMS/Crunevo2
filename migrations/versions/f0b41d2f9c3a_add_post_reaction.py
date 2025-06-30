"""add post reaction table

Revision ID: f0b41d2f9c3a
Revises: 056ac5a1f108
Create Date: 2025-07-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


def has_table(name: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


# revision identifiers, used by Alembic.
revision = "f0b41d2f9c3a"
down_revision = "056ac5a1f108"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    if not has_table("post_reaction", conn):
        op.create_table(
            "post_reaction",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False
            ),
            sa.Column(
                "post_id", sa.Integer(), sa.ForeignKey("post.id"), nullable=False
            ),
            sa.Column("reaction_type", sa.String(length=10), nullable=False),
            sa.Column("timestamp", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("user_id", "post_id", name="uniq_post_reaction"),
            if_not_exists=True,
        )


def downgrade():
    op.drop_table("post_reaction", if_exists=True)
