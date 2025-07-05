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
    with op.batch_alter_table("post", schema=None) as batch_op:
        if not has_col("post", "comment_permission", conn):
            batch_op.add_column(
                sa.Column(
                    "comment_permission",
                    sa.String(length=10),
                    nullable=False,
                    server_default="all",
                )
            )
    op.execute(
        "UPDATE post SET comment_permission='all' WHERE comment_permission IS NULL"
    )
    with op.batch_alter_table("post", schema=None) as batch_op:
        batch_op.alter_column("comment_permission", server_default=None)


def downgrade():
    with op.batch_alter_table("post", schema=None) as batch_op:
        batch_op.drop_column("comment_permission", if_exists=True)
