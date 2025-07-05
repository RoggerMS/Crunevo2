"""add event calendar fields and mission event link

Revision ID: 9b7a1e2f4c8d
Revises: add_story_model
Create Date: 2025-07-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


def has_col(table: str, column: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return any(c["name"] == column for c in inspector.get_columns(table))


revision = "9b7a1e2f4c8d"
down_revision = "add_story_model"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    with op.batch_alter_table("event") as batch_op:
        if not has_col("event", "notification_times", conn):
            batch_op.add_column(
                sa.Column("notification_times", sa.JSON(), nullable=True)
            )
        if not has_col("event", "recurring", conn):
            batch_op.add_column(
                sa.Column("recurring", sa.String(length=20), nullable=True)
            )
    with op.batch_alter_table("mission") as batch_op:
        if not has_col("mission", "event_id", conn):
            batch_op.add_column(sa.Column("event_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(None, "event", ["event_id"], ["id"])
        if not has_col("mission", "is_active", conn):
            batch_op.add_column(
                sa.Column(
                    "is_active",
                    sa.Boolean(),
                    nullable=True,
                    server_default=sa.text("true"),
                )
            )


def downgrade():
    with op.batch_alter_table("mission") as batch_op:
        batch_op.drop_column("is_active", if_exists=True)
        batch_op.drop_constraint(None, type_="foreignkey")
        batch_op.drop_column("event_id", if_exists=True)
    with op.batch_alter_table("event") as batch_op:
        batch_op.drop_column("recurring", if_exists=True)
        batch_op.drop_column("notification_times", if_exists=True)
