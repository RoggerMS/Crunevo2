"""add feed item table

Revision ID: 52d625614f92
Revises: f47bb65af23c
Create Date: 2025-06-12 05:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '52d625614f92'
down_revision = 'f47bb65af23c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'feed_item',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('item_type', sa.Enum('apunte', 'post', name='feed_item_type'), nullable=False),
        sa.Column('ref_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('feed_item')
    sa.Enum(name='feed_item_type').drop(op.get_bind())

