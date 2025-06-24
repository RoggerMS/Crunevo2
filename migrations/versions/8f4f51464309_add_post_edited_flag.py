"""add post edited flag

Revision ID: 8f4f51464309
Revises: 8728b618b1f9
Create Date: 2025-06-24 00:16:28.906872

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8f4f51464309"
down_revision = "8728b618b1f9"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("post", schema=None) as batch_op:
        batch_op.add_column(sa.Column("edited", sa.Boolean(), nullable=True))


def downgrade():
    with op.batch_alter_table("post", schema=None) as batch_op:
        batch_op.drop_column("edited")
