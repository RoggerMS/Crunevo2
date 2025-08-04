"""add api_key table"""

from alembic import op
import sqlalchemy as sa


def has_table(name: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


# revision identifiers, used by Alembic.
revision = "add_api_key"
down_revision = "b25339c3d623"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    if not has_table("api_key", conn):
        op.create_table(
            "api_key",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
            ),
            sa.Column("key", sa.String(length=64), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("key"),
            if_not_exists=True,
        )


def downgrade():
    op.drop_table("api_key", if_exists=True)
