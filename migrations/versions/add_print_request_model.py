"""add print_request table"""

from alembic import op
import sqlalchemy as sa


def has_table(name: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


revision = "add_print_request_model"
down_revision = "add_purchase_shipping_fields"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    if not has_table("print_request", conn):
        op.create_table(
            "print_request",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
            ),
            sa.Column(
                "note_id", sa.Integer(), sa.ForeignKey("note.id"), nullable=False
            ),
            sa.Column("requested_at", sa.DateTime(), nullable=True),
            sa.Column(
                "fulfilled",
                sa.Boolean(),
                nullable=True,
                server_default=sa.text("false"),
            ),
            sa.Column("fulfilled_at", sa.DateTime(), nullable=True),
            if_not_exists=True,
        )


def downgrade():
    op.drop_table("print_request", if_exists=True)
