"""add purchase and credits

Revision ID: 1a80ed700a38
Revises: e8fb5094eccf
Create Date: 2025-06-22 02:42:13.007380
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1a80ed700a38"
down_revision = "e8fb5094eccf"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "achievement",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("icon", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        if_not_exists=True,
    )

    op.create_table(
        "purchase",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column("price_soles", sa.Numeric(10, 2), nullable=True),
        sa.Column("price_credits", sa.Integer(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )

    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_cols = {c["name"] for c in insp.get_columns("product")}
    with op.batch_alter_table("product") as batch_op:
        if "price_credits" not in existing_cols:
            batch_op.add_column(sa.Column("price_credits", sa.Integer(), nullable=True))
        if "is_featured" not in existing_cols:
            batch_op.add_column(sa.Column("is_featured", sa.Boolean(), nullable=True))
        if "credits_only" not in existing_cols:
            batch_op.add_column(sa.Column("credits_only", sa.Boolean(), nullable=True))
        if "is_popular" not in existing_cols:
            batch_op.add_column(sa.Column("is_popular", sa.Boolean(), nullable=True))
        if "is_new" not in existing_cols:
            batch_op.add_column(sa.Column("is_new", sa.Boolean(), nullable=True))

    with op.batch_alter_table("user_achievement") as batch_op:
        # Solo agregar timestamp si no existe. No eliminamos earned_at aquí.
        if "timestamp" not in {c["name"] for c in insp.get_columns("user_achievement")}:
            batch_op.add_column(sa.Column("timestamp", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("user_achievement") as batch_op:
        batch_op.drop_column("timestamp", if_exists=True)
        # No re-agregamos earned_at porque nunca se eliminó

    with op.batch_alter_table("product") as batch_op:
        batch_op.drop_column("is_new", if_exists=True)
        batch_op.drop_column("is_popular", if_exists=True)
        batch_op.drop_column("credits_only", if_exists=True)
        batch_op.drop_column("is_featured", if_exists=True)
        batch_op.drop_column("price_credits", if_exists=True)

    op.drop_table("purchase", if_exists=True)
    op.drop_table("achievement", if_exists=True)
