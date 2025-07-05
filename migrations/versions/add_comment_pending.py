"""add pending flag to comments"""

from alembic import op
import sqlalchemy as sa


def has_col(table: str, column: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return any(c["name"] == column for c in inspector.get_columns(table))


revision = "add_comment_pending"
down_revision = "add_print_request_model"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    if not has_col("post_comment", "pending", conn):
        op.add_column(
            "post_comment",
            sa.Column(
                "pending",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            schema=None,
            if_not_exists=True,
        )
        op.alter_column("post_comment", "pending", server_default=None)
    if not has_col("comment", "pending", conn):
        op.add_column(
            "comment",
            sa.Column(
                "pending",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            schema=None,
            if_not_exists=True,
        )
        op.alter_column("comment", "pending", server_default=None)


def downgrade():
    with op.batch_alter_table("post_comment", schema=None) as batch_op:
        batch_op.drop_column("pending", if_exists=True)
    with op.batch_alter_table("comment", schema=None) as batch_op:
        batch_op.drop_column("pending", if_exists=True)
