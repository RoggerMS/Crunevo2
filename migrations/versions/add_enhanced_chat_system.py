"""Add enhanced chat system

Revision ID: enhanced_chat_2025
Revises: f0b41d2f9c3a
Create Date: 2025-06-28 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


def has_col(table: str, column: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return any(c["name"] == column for c in inspector.get_columns(table))


# revision identifiers, used by Alembic.
revision = "enhanced_chat_2025"
down_revision = "f0b41d2f9c3a"
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to Message table
    conn = op.get_bind()
    with op.batch_alter_table("message", schema=None) as batch_op:
        if not has_col("message", "is_global", conn):
            batch_op.add_column(sa.Column("is_global", sa.Boolean(), nullable=True))
        if not has_col("message", "is_read", conn):
            batch_op.add_column(sa.Column("is_read", sa.Boolean(), nullable=True))
        if not has_col("message", "is_deleted", conn):
            batch_op.add_column(sa.Column("is_deleted", sa.Boolean(), nullable=True))
        batch_op.alter_column("receiver_id", nullable=True)
        batch_op.alter_column("content", nullable=False)

    # Update existing data
    op.execute(
        "UPDATE message SET is_global = false, is_read = false, is_deleted = false WHERE is_global IS NULL"
    )

    # Create ChatRoom table
    op.create_table(
        "chat_room",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )


def downgrade():
    op.drop_table("chat_room")

    with op.batch_alter_table("message", schema=None) as batch_op:
        batch_op.drop_column("is_deleted", if_exists=True)
        batch_op.drop_column("is_read", if_exists=True)
        batch_op.drop_column("is_global", if_exists=True)
        batch_op.alter_column("receiver_id", nullable=False)
