"""Merge migration heads

Revision ID: 5683aa47fe36
Revises: add_mostrar_tienda_perfil, add_product_is_official
Create Date: 2025-08-06 18:06:37.906308

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5683aa47fe36'
down_revision = ('add_mostrar_tienda_perfil', 'add_product_is_official')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
