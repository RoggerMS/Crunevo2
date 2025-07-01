"""add post images table"""

from alembic import op
import sqlalchemy as sa

revision = "add_post_images"
down_revision = "complete_missing_models"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "post_image" not in inspector.get_table_names():
        op.create_table(
            "post_image",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "post_id", sa.Integer(), sa.ForeignKey("post.id"), nullable=False
            ),
            sa.Column("url", sa.String(length=255), nullable=False),
            if_not_exists=True,
        )


def downgrade():
    op.drop_table("post_image", if_exists=True)
