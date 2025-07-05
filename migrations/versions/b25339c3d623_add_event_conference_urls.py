"""add event conference urls

Revision ID: b25339c3d623
Revises: add_comment_pending
Create Date: 2025-07-05 16:40:15.428519

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b25339c3d623"
down_revision = "add_comment_pending"
branch_labels = None
depends_on = None


def has_col(table: str, column: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return any(c["name"] == column for c in inspector.get_columns(table))


def upgrade():
    conn = op.get_bind()
    with op.batch_alter_table("event") as batch_op:
        if not has_col("event", "jitsi_url", conn):
            batch_op.add_column(
                sa.Column("jitsi_url", sa.String(length=255), nullable=True)
            )
        if not has_col("event", "zoom_url", conn):
            batch_op.add_column(
                sa.Column("zoom_url", sa.String(length=255), nullable=True)
            )


def downgrade():
    with op.batch_alter_table("event") as batch_op:
        batch_op.drop_column("zoom_url", if_exists=True)
        batch_op.drop_column("jitsi_url", if_exists=True)
