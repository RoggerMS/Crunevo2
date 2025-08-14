"""Add is_featured column to personal_space_blocks

Revision ID: add_is_featured_personal_space
Revises: add_personal_space
Create Date: 2025-01-13 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_is_featured_personal_space'
down_revision = 'add_personal_space'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_featured column to personal_space_blocks table
    op.add_column('personal_space_blocks', sa.Column('is_featured', sa.Boolean(), nullable=False, default=False))
    
    # Update existing records to have is_featured = False
    op.execute("UPDATE personal_space_blocks SET is_featured = 0 WHERE is_featured IS NULL")


def downgrade():
    # Remove is_featured column
    op.drop_column('personal_space_blocks', 'is_featured')