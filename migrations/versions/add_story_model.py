"""add story table"""

from alembic import op
import sqlalchemy as sa


def has_table(name: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


revision = "add_story_model"
down_revision = "99588ab3c722"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    if not has_table("story", conn):
        op.create_table(
            "story",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
            ),
            sa.Column("image_url", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            if_not_exists=True,
        )


def downgrade():
    op.drop_table("story", if_exists=True)
