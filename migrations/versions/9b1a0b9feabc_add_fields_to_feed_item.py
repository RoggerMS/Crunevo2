"""add fields to feed item

Revision ID: 9b1a0b9feabc
Revises: 52d625614f92
Create Date: 2025-06-12 05:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '9b1a0b9feabc'
down_revision = '52d625614f92'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        for val in ['logro', 'evento', 'movimiento', 'mensaje']:
            op.execute(f"ALTER TYPE feed_item_type ADD VALUE IF NOT EXISTS '{val}'")
    op.add_column('feed_item', sa.Column('is_highlight', sa.Boolean(), server_default=sa.text('0'), nullable=True))
    op.add_column('feed_item', sa.Column('metadata', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('feed_item', 'metadata')
    op.drop_column('feed_item', 'is_highlight')
    # Enum contraction skipped
