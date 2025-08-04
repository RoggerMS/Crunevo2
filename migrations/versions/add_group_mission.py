"""add group mission tables"""

from alembic import op
import sqlalchemy as sa


def has_table(name: str, conn) -> bool:
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


# revision identifiers, used by Alembic.
revision = "add_group_mission"
down_revision = "2ae2987611ab"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    if not has_table("group_mission", conn):
        op.create_table(
            "group_mission",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("code", sa.String(length=50), nullable=False, unique=True),
            sa.Column("description", sa.String(length=200), nullable=False),
            sa.Column("goal", sa.Integer(), nullable=True),
            sa.Column("credit_reward", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column(
                "is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")
            ),
            if_not_exists=True,
        )
    if not has_table("group_mission_participant", conn):
        op.create_table(
            "group_mission_participant",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
            ),
            sa.Column(
                "group_mission_id",
                sa.Integer(),
                sa.ForeignKey("group_mission.id"),
                nullable=False,
            ),
            sa.Column("progress", sa.Integer(), nullable=True, server_default="0"),
            sa.Column(
                "claimed", sa.Boolean(), nullable=True, server_default=sa.text("false")
            ),
            if_not_exists=True,
        )


def downgrade():
    op.drop_table("group_mission_participant", if_exists=True)
    op.drop_table("group_mission", if_exists=True)
