"""add internship models

Revision ID: add_internship_models
Revises: 4c29ad8b8c1a
Create Date: 2025-12-31 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


def has_table(name: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


revision = "add_internship_models"
down_revision = "4c29ad8b8c1a"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    if not has_table("internship", conn):
        op.create_table(
            "internship",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("field", sa.String(length=100), nullable=True),
            sa.Column("location", sa.String(length=100), nullable=True),
            sa.Column("company", sa.String(length=100), nullable=True),
            sa.Column("posted_at", sa.DateTime(), nullable=True),
            if_not_exists=True,
        )
    if not has_table("internship_application", conn):
        op.create_table(
            "internship_application",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "internship_id",
                sa.Integer(),
                sa.ForeignKey("internship.id"),
                nullable=False,
            ),
            sa.Column(
                "user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False
            ),
            sa.Column("cover_letter", sa.Text(), nullable=True),
            sa.Column("applied_at", sa.DateTime(), nullable=True),
            if_not_exists=True,
        )


def downgrade():
    op.drop_table("internship_application", if_exists=True)
    op.drop_table("internship", if_exists=True)
