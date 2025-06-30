"""Add third phase models: certificates, club posts, event participation, saved content

Revision ID: third_phase_2024
Revises: new_sections_2024
Create Date: 2024-01-15 15:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


def has_table(name: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


# revision identifiers
revision = "third_phase_2024"
down_revision = "new_sections_2024"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    # Create certificate table
    if not has_table("certificate", conn):
        op.create_table(
            "certificate",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("certificate_type", sa.String(length=50), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("issued_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["user.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
            if_not_exists=True,
        )

    # Create club_post table
    if not has_table("club_post", conn):
        op.create_table(
            "club_post",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("club_id", sa.Integer(), nullable=False),
            sa.Column("author_id", sa.Integer(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("likes", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(
                ["author_id"],
                ["user.id"],
            ),
            sa.ForeignKeyConstraint(
                ["club_id"],
                ["club.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
            if_not_exists=True,
        )

    # Create event_participation table
    if not has_table("event_participation", conn):
        op.create_table(
            "event_participation",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("event_id", sa.Integer(), nullable=False),
            sa.Column("joined_at", sa.DateTime(), nullable=True),
            sa.Column("attended", sa.Boolean(), nullable=True),
            sa.ForeignKeyConstraint(
                ["event_id"],
                ["event.id"],
            ),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["user.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
            if_not_exists=True,
        )

    # Create saved_content table
    if not has_table("saved_content", conn):
        op.create_table(
            "saved_content",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("content_type", sa.String(length=20), nullable=False),
            sa.Column("content_id", sa.Integer(), nullable=False),
            sa.Column("saved_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["user.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "content_type", "content_id"),
            if_not_exists=True,
        )


def downgrade():
    op.drop_table("saved_content", if_exists=True)
    op.drop_table("event_participation", if_exists=True)
    op.drop_table("club_post", if_exists=True)
    op.drop_table("certificate", if_exists=True)
