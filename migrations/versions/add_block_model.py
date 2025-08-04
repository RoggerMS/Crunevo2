"""Add Block model"""

from alembic import op
import sqlalchemy as sa

revision = "add_block_model"
down_revision = "bdd3abdf7084"
branch_labels = None
depends_on = None


def has_table(name: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


def upgrade():
    conn = op.get_bind()
    if not has_table("blocks", conn):
        op.execute(sa.text("DROP SEQUENCE IF EXISTS blocks_id_seq CASCADE"))
        op.create_table(
            "blocks",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
            ),
            sa.Column("type", sa.String(length=50), nullable=False),
            sa.Column(
                "title", sa.String(length=255), nullable=True, default="Nuevo bloque"
            ),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column(
                "metadata", sa.JSON(), nullable=True, server_default=sa.text("'{}'")
            ),
            sa.Column(
                "is_featured",
                sa.Boolean(),
                nullable=True,
                server_default=sa.text("false"),
            ),
            sa.Column(
                "order_index", sa.Integer(), nullable=True, server_default=sa.text("0")
            ),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            if_not_exists=True,
        )
        op.create_index(op.f("ix_blocks_user_id"), "blocks", ["user_id"], unique=False)
        op.create_index(
            op.f("ix_blocks_order_index"), "blocks", ["order_index"], unique=False
        )


def downgrade():
    op.drop_index(op.f("ix_blocks_order_index"), table_name="blocks")
    op.drop_index(op.f("ix_blocks_user_id"), table_name="blocks")
    op.drop_table("blocks", if_exists=True)
