"""Add requires_review columns to forum tables

Revision ID: forum_requires_review_column
Revises: forum_modernization_schema
Create Date: 2024-09-15 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = "forum_requires_review_column"
down_revision = "c0f842e75a5a"
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

    if has_table("forum_question", conn) and not has_column(
        "forum_question", "requires_review", conn
    ):
        op.add_column(
            "forum_question",
            sa.Column(
                "requires_review",
                sa.Boolean(),
                server_default=sa.text("false"),
                nullable=False,
            ),
        )

    if has_table("forum_answer", conn) and not has_column(
        "forum_answer", "requires_review", conn
    ):
        op.add_column(
            "forum_answer",
            sa.Column(
                "requires_review",
                sa.Boolean(),
                server_default=sa.text("false"),
                nullable=False,
            ),
        )


def downgrade():
    conn = op.get_bind()

    if has_table("forum_question", conn) and has_column(
        "forum_question", "requires_review", conn
    ):
        op.drop_column("forum_question", "requires_review")

    if has_table("forum_answer", conn) and has_column(
        "forum_answer", "requires_review", conn
    ):
        op.drop_column("forum_answer", "requires_review")
