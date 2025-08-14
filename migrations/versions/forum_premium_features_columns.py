"""Add premium feature columns to forum tables

Revision ID: forum_premium_features_columns
Revises: forum_requires_review_column
Create Date: 2025-08-14 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = "forum_premium_features_columns"
down_revision = "forum_requires_review_column"
branch_labels = None
depends_on = None


def has_table(name: str, conn) -> bool:
    inspector = Inspector.from_engine(conn)
    return name in inspector.get_table_names()


def has_column(table_name: str, column_name: str, conn) -> bool:
    inspector = Inspector.from_engine(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    conn = op.get_bind()

    if has_table("forum_question", conn):
        if not has_column("forum_question", "is_boosted", conn):
            op.add_column(
                "forum_question",
                sa.Column(
                    "is_boosted",
                    sa.Boolean(),
                    server_default=sa.text("false"),
                    nullable=False,
                ),
            )
        if not has_column("forum_question", "boost_expires", conn):
            op.add_column("forum_question", sa.Column("boost_expires", sa.DateTime()))

    if has_table("forum_answer", conn):
        if not has_column("forum_answer", "is_highlighted", conn):
            op.add_column(
                "forum_answer",
                sa.Column(
                    "is_highlighted",
                    sa.Boolean(),
                    server_default=sa.text("false"),
                    nullable=False,
                ),
            )
        if not has_column("forum_answer", "highlight_expires", conn):
            op.add_column("forum_answer", sa.Column("highlight_expires", sa.DateTime()))


def downgrade():
    conn = op.get_bind()

    if has_table("forum_answer", conn):
        if has_column("forum_answer", "highlight_expires", conn):
            op.drop_column("forum_answer", "highlight_expires")
        if has_column("forum_answer", "is_highlighted", conn):
            op.drop_column("forum_answer", "is_highlighted")

    if has_table("forum_question", conn):
        if has_column("forum_question", "boost_expires", conn):
            op.drop_column("forum_question", "boost_expires")
        if has_column("forum_question", "is_boosted", conn):
            op.drop_column("forum_question", "is_boosted")
