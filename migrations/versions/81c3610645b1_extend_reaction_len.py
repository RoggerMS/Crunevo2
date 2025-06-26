"""extend reaction_type length

Revision ID: 81c3610645b1
Revises: f0b41d2f9c3a
Create Date: 2025-07-01 00:01:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "81c3610645b1"
down_revision = "f0b41d2f9c3a"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("post_reaction", recreate="always") as batch:
        batch.alter_column("reaction_type", type_=sa.String(length=20))


def downgrade():
    with op.batch_alter_table("post_reaction", recreate="always") as batch:
        batch.alter_column("reaction_type", type_=sa.String(length=10))
