"""Placeholder migration to satisfy missing revision

Revision ID: cd14a01e631b
Revises: 056ac5a1f108
Create Date: 2025-08-06 00:00:00.000000
"""

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

# revision identifiers, used by Alembic.
revision = "cd14a01e631b"
down_revision = "056ac5a1f108"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
