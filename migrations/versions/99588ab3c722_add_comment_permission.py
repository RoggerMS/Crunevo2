"""add comment permission to post

Revision ID: 99588ab3c722
Revises: f0b41d2f9c3a
Create Date: 2025-07-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


def has_col(table: str, column: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return any(c["name"] == column for c in inspector.get_columns(table))


# revision identifiers, used by Alembic.
revision = "99588ab3c722"
down_revision = "add_page_view"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    added = False
    if not has_col("post", "comment_permission", conn):
        op.add_column(
            "post",
            sa.Column(
                "comment_permission",
                sa.String(length=10),
                nullable=False,
                server_default="all",
            ),
            schema=None,
            if_not_exists=True,
        )
        added = True

    if added:
        op.execute(
            "UPDATE post SET comment_permission='all' WHERE comment_permission IS NULL"
        )
        op.alter_column(
            "post",
            "comment_permission",
            server_default=None,
            schema=None,
        )


def downgrade():
    with op.batch_alter_table("post", schema=None) as batch_op:
        batch_op.drop_column("comment_permission", if_exists=True)
