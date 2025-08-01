"""Add club banner, social links and creator fields

Revision ID: club_modernization_2025
Revises: new_sections_2024
Create Date: 2025-01-20 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = "club_modernization_2025"
down_revision = "new_sections_2024"
branch_labels = None
depends_on = None


def has_column(table_name, column_name, conn):
    """Check if a table has a specific column"""
    inspector = Inspector.from_engine(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    """Add banner_url, facebook_url, whatsapp_url and creator_id to club table"""
    conn = op.get_bind()

    # Add banner_url column if it doesn't exist
    if not has_column("club", "banner_url", conn):
        op.add_column(
            "club", sa.Column("banner_url", sa.String(length=255), nullable=True)
        )

    # Add facebook_url column if it doesn't exist
    if not has_column("club", "facebook_url", conn):
        op.add_column(
            "club", sa.Column("facebook_url", sa.String(length=255), nullable=True)
        )

    # Add whatsapp_url column if it doesn't exist
    if not has_column("club", "whatsapp_url", conn):
        op.add_column(
            "club", sa.Column("whatsapp_url", sa.String(length=255), nullable=True)
        )

    # Add creator_id column if it doesn't exist
    if not has_column("club", "creator_id", conn):
        # First add the column as nullable
        op.add_column("club", sa.Column("creator_id", sa.Integer(), nullable=True))

        # Set default creator_id to the first admin of each club (if any)
        op.execute(
            """
            UPDATE club 
            SET creator_id = (
                SELECT cm.user_id 
                FROM club_member cm 
                WHERE cm.club_id = club.id 
                AND cm.role = 'admin' 
                LIMIT 1
            )
            WHERE creator_id IS NULL
        """
        )

        # If no admin found, set to the first member
        op.execute(
            """
            UPDATE club 
            SET creator_id = (
                SELECT cm.user_id 
                FROM club_member cm 
                WHERE cm.club_id = club.id 
                ORDER BY cm.joined_at ASC 
                LIMIT 1
            )
            WHERE creator_id IS NULL
        """
        )

        # Now make it non-nullable and add foreign key
        op.alter_column("club", "creator_id", nullable=False)
        op.create_foreign_key(
            "fk_club_creator_id", "club", "user", ["creator_id"], ["id"]
        )


def downgrade():
    """Remove banner_url, facebook_url, whatsapp_url and creator_id from club table"""

    # Drop foreign key constraint first
    try:
        op.drop_constraint("fk_club_creator_id", "club", type_="foreignkey")
    except Exception:
        pass

    # Drop columns
    try:
        op.drop_column("club", "creator_id")
    except Exception:
        pass

    try:
        op.drop_column("club", "whatsapp_url")
    except Exception:
        pass

    try:
        op.drop_column("club", "facebook_url")
    except Exception:
        pass

    try:
        op.drop_column("club", "banner_url")
    except Exception:
        pass
