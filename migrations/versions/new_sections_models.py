"""Add club, forum and event models

Revision ID: new_sections_2024
Revises: abcd1234add
Create Date: 2024-01-15 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


def has_table(name: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


# revision identifiers
revision = "new_sections_2024"
down_revision = "abcd1234add"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    # Create club table
    if not has_table("club", conn):
        op.create_table(
            "club",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("career", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("avatar_url", sa.String(length=255), nullable=True),
            sa.Column("member_count", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            if_not_exists=True,
        )

    # Create club_member table
    if not has_table("club_member", conn):
        op.create_table(
            "club_member",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("club_id", sa.Integer(), nullable=False),
            sa.Column("joined_at", sa.DateTime(), nullable=True),
            sa.Column("role", sa.String(length=20), nullable=True),
            sa.ForeignKeyConstraint(
                ["club_id"],
                ["club.id"],
            ),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
            if_not_exists=True,
        )

    # Create forum_question table
    if not has_table("forum_question", conn):
        op.create_table(
            "forum_question",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("category", sa.String(length=50), nullable=False),
            sa.Column("author_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.Column("views", sa.Integer(), nullable=True),
            sa.Column("is_solved", sa.Boolean(), nullable=True),
            sa.ForeignKeyConstraint(
                ["author_id"],
                ["users.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
            if_not_exists=True,
        )

    # Create forum_answer table
    if not has_table("forum_answer", conn):
        op.create_table(
            "forum_answer",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("question_id", sa.Integer(), nullable=False),
            sa.Column("author_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.Column("is_accepted", sa.Boolean(), nullable=True),
            sa.Column("votes", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(
                ["author_id"],
                ["users.id"],
            ),
            sa.ForeignKeyConstraint(
                ["question_id"],
                ["forum_question.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
            if_not_exists=True,
        )

    # Create event table
    if not has_table("event", conn):
        op.create_table(
            "event",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("event_date", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("image_url", sa.String(length=255), nullable=True),
            sa.Column("is_featured", sa.Boolean(), nullable=True),
            sa.Column("rewards", sa.Text(), nullable=True),
            sa.Column("category", sa.String(length=50), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            if_not_exists=True,
        )


def downgrade():
    op.drop_table("event", if_exists=True)
    op.drop_table("forum_answer", if_exists=True)
    op.drop_table("forum_question", if_exists=True)
    op.drop_table("club_member", if_exists=True)
    op.drop_table("club", if_exists=True)
