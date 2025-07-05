"""add site_config table"""

from alembic import op
import sqlalchemy as sa


def has_table(name: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


# revision identifiers, used by Alembic.
revision = "add_site_config"
down_revision = "add_user_activity"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    if not has_table("site_config", conn):
        op.create_table(
            "site_config",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("key", sa.String(length=50), nullable=False, unique=True),
            sa.Column("value", sa.String(length=255), nullable=True),
            if_not_exists=True,
        )


def downgrade():
    op.drop_table("site_config", if_exists=True)
