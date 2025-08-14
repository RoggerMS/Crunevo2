"""Add mostrar_tienda_perfil field to User model

Revision ID: add_mostrar_tienda_perfil
Revises: 
Create Date: 2025-08-06 18:03:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = "add_mostrar_tienda_perfil"
down_revision = None
branch_labels = None
depends_on = None


def has_column(table_name, column_name, conn):
    inspector = Inspector.from_engine(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    conn = op.get_bind()
    with op.batch_alter_table("user", schema=None) as batch_op:
        if not has_column("user", "mostrar_tienda_perfil", conn):
            batch_op.add_column(
                sa.Column(
                    "mostrar_tienda_perfil", sa.Boolean(), nullable=True, default=False
                )
            )


def downgrade():
    conn = op.get_bind()
    with op.batch_alter_table("user", schema=None) as batch_op:
        if has_column("user", "mostrar_tienda_perfil", conn):
            batch_op.drop_column("mostrar_tienda_perfil")
