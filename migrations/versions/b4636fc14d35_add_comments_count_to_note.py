"""add comments_count to note

Revision ID: b4636fc14d35
Revises: 1c2d3e4f
Create Date: 2025-07-01 00:00:00

"""

from alembic import op
import sqlalchemy as sa

revision = "b4636fc14d35"
down_revision = "1c2d3e4f"

def upgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
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
    """))

def downgrade():
    op.drop_column("note", "comments_count")
