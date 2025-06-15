"""add comments_count to note

Revision ID: b4636fc14d35
Revises: 1c2d3e4f
Create Date: 2025-07-01 00:00:00

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b4636fc14d35"
down_revision = "1c2d3e4f"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name='note' AND column_name='comments_count'
        ) THEN
            ALTER TABLE note ADD COLUMN comments_count INTEGER DEFAULT 0;
        END IF;
    END$$;
    """)
    # Limpieza del default en PostgreSQL
    if conn.dialect.name == "postgresql":
        conn.execute("ALTER TABLE note ALTER COLUMN comments_count DROP DEFAULT;")



def downgrade():
    op.drop_column("note", "comments_count")
