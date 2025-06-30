"""add post edited flag

Revision ID: 8f4f51464309
Revises: 8728b618b1f9
Create Date: 2025-06-24 00:16:28.906872

"""

from alembic import op
import sqlalchemy as sa


def has_col(table: str, column: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return any(c["name"] == column for c in inspector.get_columns(table))


# revision identifiers, used by Alembic.
revision = "8f4f51464309"
down_revision = "8728b618b1f9"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    with op.batch_alter_table("post", schema=None) as batch_op:
        if not has_col("post", "edited", conn):
            batch_op.add_column(sa.Column("edited", sa.Boolean(), nullable=True))


def downgrade():
    with op.batch_alter_table("post", schema=None) as batch_op:
        batch_op.drop_column("edited", if_exists=True)
