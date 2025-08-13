"""Fix JSONB compatibility for SQLite

Revision ID: c0f842e75a5a
Revises: bfe408324362
Create Date: 2025-08-13 13:35:45.880104

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c0f842e75a5a'
down_revision = 'bfe408324362'
branch_labels = None
depends_on = None


def upgrade():
    # Fix JSONB columns to use JSON for SQLite compatibility
    # This migration handles the conversion from postgresql.JSONB to sa.JSON
    
    # For personal_space_blocks table
    with op.batch_alter_table('personal_space_blocks', schema=None) as batch_op:
        batch_op.alter_column('metadata',
                              existing_type=sa.Text(),
                              type_=sa.JSON(),
                              existing_nullable=True)
    
    # For personal_space_templates table
    with op.batch_alter_table('personal_space_templates', schema=None) as batch_op:
        batch_op.alter_column('template_data',
                              existing_type=sa.Text(),
                              type_=sa.JSON(),
                              existing_nullable=False)
    
    # For personal_space_analytics_events table
    with op.batch_alter_table('personal_space_analytics_events', schema=None) as batch_op:
        batch_op.alter_column('event_data',
                              existing_type=sa.Text(),
                              type_=sa.JSON(),
                              existing_nullable=True)


def downgrade():
    # Revert JSON columns back to Text (since we can't go back to JSONB in SQLite)
    
    # For personal_space_blocks table
    with op.batch_alter_table('personal_space_blocks', schema=None) as batch_op:
        batch_op.alter_column('metadata',
                              existing_type=sa.JSON(),
                              type_=sa.Text(),
                              existing_nullable=True)
    
    # For personal_space_templates table
    with op.batch_alter_table('personal_space_templates', schema=None) as batch_op:
        batch_op.alter_column('template_data',
                              existing_type=sa.JSON(),
                              type_=sa.Text(),
                              existing_nullable=False)
    
    # For personal_space_analytics_events table
    with op.batch_alter_table('personal_space_analytics_events', schema=None) as batch_op:
        batch_op.alter_column('event_data',
                              existing_type=sa.JSON(),
                              type_=sa.Text(),
                              existing_nullable=True)
