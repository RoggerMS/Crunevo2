"""add user_block table and message attachment_url column

Revision ID: user_block_attachment
Revises: add_story_model
Create Date: 2025-07-15 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


def has_table(name: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


def has_col(table: str, column: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return any(c["name"] == column for c in inspector.get_columns(table))


revision = "user_block_attachment"
down_revision = "2ae2987611ab"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    if not has_table("user_block", conn):
        # drop leftover sequence from aborted attempts to avoid duplicate
        # sequence errors when creating the table
        op.execute(sa.text("DROP SEQUENCE IF EXISTS user_block_id_seq CASCADE"))
        op.create_table(
            "user_block",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "blocker_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
            ),
            sa.Column(
                "blocked_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
            ),
            sa.UniqueConstraint("blocker_id", "blocked_id", name="uniq_user_block"),
            if_not_exists=True,
        )
    if not has_col("message", "attachment_url", conn):
        op.add_column(
            "message",
            sa.Column("attachment_url", sa.String(length=255), nullable=True),
            schema=None,
            if_not_exists=True,
        )


def downgrade():
    with op.batch_alter_table("message", schema=None) as batch_op:
        batch_op.drop_column("attachment_url", if_exists=True)
    op.drop_table("user_block", if_exists=True)
