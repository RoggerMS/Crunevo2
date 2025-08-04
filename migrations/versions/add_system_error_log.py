"""create system error log table

Revision ID: add_system_error_log
Revises: user_block_attachment
Create Date: 2025-07-30 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_system_error_log"
down_revision = "add_block_model"
branch_labels = None
depends_on = None


def has_table(name: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


def upgrade():
    conn = op.get_bind()
    if not has_table("system_error_log", conn):
        op.create_table(
            "system_error_log",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("timestamp", sa.DateTime(), nullable=True),
            sa.Column("ruta", sa.String(length=255), nullable=True),
            sa.Column("mensaje", sa.Text(), nullable=True),
            sa.Column("status_code", sa.Integer(), nullable=True),
            sa.Column(
                "user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True
            ),
            sa.Column(
                "resuelto", sa.Boolean(), nullable=True, server_default=sa.text("false")
            ),
            if_not_exists=True,
        )


def downgrade():
    op.drop_table("system_error_log", if_exists=True)
