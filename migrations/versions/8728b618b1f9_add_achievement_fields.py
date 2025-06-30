"""add achievement fields

Revision ID: 8728b618b1f9
Revises: b1b2b3b4c5d6
Create Date: 2025-06-23 02:16:47.197015

"""

from alembic import op
import sqlalchemy as sa


def has_col(table: str, column: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return any(c["name"] == column for c in inspector.get_columns(table))


# revision identifiers, used by Alembic.
revision = "8728b618b1f9"
down_revision = "b1b2b3b4c5d6"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    with op.batch_alter_table("achievement") as batch_op:
        if not has_col("achievement", "description", conn):
            batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
        if not has_col("achievement", "created_at", conn):
            batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=True))

    with op.batch_alter_table("user_achievement") as batch_op:
        if not has_col("user_achievement", "achievement_id", conn):
            batch_op.add_column(
                sa.Column("achievement_id", sa.Integer(), nullable=True)
            )
            batch_op.create_foreign_key(
                "fk_userach_achievement",
                "achievement",
                ["achievement_id"],
                ["id"],
            )


def downgrade():
    with op.batch_alter_table("user_achievement") as batch_op:
        batch_op.drop_constraint(
            "fk_userach_achievement", type_="foreignkey", if_exists=True
        )
        batch_op.drop_column("achievement_id", if_exists=True)

    with op.batch_alter_table("achievement") as batch_op:
        batch_op.drop_column("created_at", if_exists=True)
        batch_op.drop_column("description", if_exists=True)
