"""Complete missing models and relationships

Revision ID: complete_missing_models
Revises: add_courses_system
Create Date: 2024-12-28 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "complete_missing_models"
down_revision = "add_courses_system"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    def has_col(table: str, column: str) -> bool:
        return any(c["name"] == column for c in inspector.get_columns(table))

    if not has_col("users", "pref_dark"):
        op.add_column(
            "users",
            sa.Column("pref_dark", sa.Boolean(), server_default=sa.text("false")),
        )
    if not has_col("users", "bio"):
        op.add_column("users", sa.Column("bio", sa.Text()))
    if not has_col("users", "career"):
        op.add_column("users", sa.Column("career", sa.String(100)))
    if not has_col("users", "interests"):
        op.add_column("users", sa.Column("interests", sa.Text()))

    if not has_col("product", "active"):
        op.add_column(
            "product",
            sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
        )
    if not has_col("product", "popularity_score"):
        op.add_column(
            "product",
            sa.Column("popularity_score", sa.Integer(), server_default="0"),
        )

    op.create_table(
        "club_member",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("club_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(20), server_default="member"),
        sa.Column("joined_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["club_id"], ["club.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "club_id"),
        if_not_exists=True,
    )

    op.create_table(
        "saved_course",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("saved_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "course_id"),
        if_not_exists=True,
    )


def downgrade():
    op.drop_table("saved_course", if_exists=True)
    op.drop_table("club_member", if_exists=True)
    op.drop_column("product", "popularity_score", if_exists=True)
    op.drop_column("product", "active", if_exists=True)
    op.drop_column("users", "interests", if_exists=True)
    op.drop_column("users", "career", if_exists=True)
    op.drop_column("users", "bio", if_exists=True)
    op.drop_column("users", "pref_dark", if_exists=True)
