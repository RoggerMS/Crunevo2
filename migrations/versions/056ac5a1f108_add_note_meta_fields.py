"""add note meta fields

Revision ID: 056ac5a1f108
Revises: 8f4f51464309
Create Date: 2025-06-26 00:45:49.193265

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "056ac5a1f108"
down_revision = "8f4f51464309"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("note", schema=None) as batch_op:
        batch_op.add_column(sa.Column("language", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("reading_time", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("content_type", sa.String(length=20), nullable=True)
        )
        batch_op.add_column(sa.Column("summary", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("course", sa.String(length=140), nullable=True))
        batch_op.add_column(sa.Column("career", sa.String(length=140), nullable=True))


def downgrade():
    with op.batch_alter_table("note", schema=None) as batch_op:
        batch_op.drop_column("career")
        batch_op.drop_column("course")
        batch_op.drop_column("summary")
        batch_op.drop_column("content_type")
        batch_op.drop_column("reading_time")
        batch_op.drop_column("language")
