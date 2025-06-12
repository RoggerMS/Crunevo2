"""store full argon2 hashes in text field

Revision ID: 76b3ec100daa
Revises: 99a8443c7f1f
Create Date: 2025-06-12 17:10:18.143261
"""

from alembic import op
import sqlalchemy as sa

revision = "76b3ec100daa"
down_revision = "99a8443c7f1f"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column("password_hash", type_=sa.Text())


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column("password_hash", type_=sa.String(length=128))
