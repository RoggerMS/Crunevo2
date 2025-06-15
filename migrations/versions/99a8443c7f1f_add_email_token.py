from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "99a8443c7f1f"
down_revision = "c789abc12345"
branch_labels = None
depends_on = None


def upgrade():
    # Verificar si la tabla 'email_token' ya existe
    conn = op.get_bind()
    result = conn.execute(
        text(
            "SELECT to_regclass('public.email_token')"
        )
    )
    table_exists = result.scalar()

    if not table_exists:
        op.create_table(
            "email_token",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("token", sa.String(length=64), nullable=False),
            sa.Column("email", sa.String(length=120), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("consumed_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token"),
        )

    # Agregar columna "activated" a la tabla "user" si no existe
    insp = sa.inspect(conn)
    user_columns = [col["name"] for col in insp.get_columns("user")]
    if "activated" not in user_columns:
        with op.batch_alter_table("user", schema=None) as batch_op:
            batch_op.add_column(sa.Column("activated", sa.Boolean(), nullable=True))


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("activated")

    op.drop_table("email_token")
