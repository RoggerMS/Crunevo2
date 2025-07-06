
"""Add career module support

Revision ID: add_career_module
Revises: add_personal_space
Create Date: 2025-01-05 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_career_module'
down_revision = 'add_personal_space'
branch_labels = None
depends_on = None


def upgrade():
    # Add any career-specific database changes if needed
    # For now, we're using existing models (User.career, etc.)
    # so no schema changes are required
    
    # Update existing courses to have category matching careers
    op.execute("""
        UPDATE courses 
        SET category = 'Ingeniería de Sistemas' 
        WHERE category IS NULL OR category = 'programming'
    """)
    
    # Update existing clubs to have career field
    op.execute("""
        UPDATE club 
        SET career = 'Ingeniería de Sistemas' 
        WHERE career IS NULL OR career = ''
    """)


def downgrade():
    # Reverse the changes if needed
    pass
