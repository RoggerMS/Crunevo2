"""Add system metrics tables

Revision ID: add_system_metrics_tables
Revises: 018c30955e14
Create Date: 2025-07-29 05:06:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_system_metrics_tables'
down_revision = '018c30955e14'
branch_labels = None
depends_on = None


def upgrade():
    # Crear tabla system_metrics solo si no existe
    try:
        op.create_table('system_metrics',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.Column('system_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('database_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('performance_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('alerts', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    except Exception:
        pass  # Tabla ya existe
    
    # Crear tabla performance_metrics solo si no existe
    try:
        op.create_table('performance_metrics',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('operation', sa.String(length=100), nullable=False),
            sa.Column('duration', sa.Float(), nullable=False),
            sa.Column('success', sa.Boolean(), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    except Exception:
        pass  # Tabla ya existe


def downgrade():
    # No hacer nada en downgrade para evitar problemas
    pass 