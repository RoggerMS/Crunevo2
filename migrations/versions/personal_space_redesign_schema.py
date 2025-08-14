"""Personal Space Redesign Schema

Revision ID: personal_space_redesign_schema
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = "personal_space_redesign_schema"
down_revision = None
branch_labels = None
depends_on = None


def has_table(name: str, conn) -> bool:
    inspector = Inspector.from_engine(conn)
    return name in inspector.get_table_names()


def upgrade():
    conn = op.get_bind()
    if has_table("personal_space_blocks", conn):
        return

    # Create personal_space_blocks table with enhanced structure
    op.create_table(
        "personal_space_blocks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column(
            "metadata",
            sa.JSON(),
            nullable=True,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "order_index", sa.Integer(), nullable=True, server_default=sa.text("0")
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=True,
            server_default=sa.text("'active'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("NOW()"),
        ),
        sa.CheckConstraint(
            "type IN ('tarea', 'nota', 'kanban', 'objetivo', 'bitacora', 'enlace', 'frase', 'recordatorio', 'meta', 'lista', 'nota_enriquecida', 'bloque_personalizado')",
            name="check_block_type",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'completed', 'archived', 'deleted')",
            name="check_block_status",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for optimization
    op.create_index(
        "idx_personal_space_blocks_user_id", "personal_space_blocks", ["user_id"]
    )
    op.create_index("idx_personal_space_blocks_type", "personal_space_blocks", ["type"])
    op.create_index(
        "idx_personal_space_blocks_status", "personal_space_blocks", ["status"]
    )
    op.create_index(
        "idx_personal_space_blocks_order",
        "personal_space_blocks",
        ["user_id", "order_index"],
    )
    op.create_index(
        "idx_personal_space_blocks_updated_at",
        "personal_space_blocks",
        ["updated_at"],
        postgresql_using="btree",
        postgresql_ops={"updated_at": "DESC"},
    )

    # Create GIN index for JSONB metadata
    op.create_index(
        "idx_personal_space_blocks_metadata",
        "personal_space_blocks",
        ["metadata"],
        postgresql_using="gin",
    )

    # Create personal_space_templates table
    op.create_table(
        "personal_space_templates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("template_data", sa.JSON(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column(
            "is_public", sa.Boolean(), nullable=True, server_default=sa.text("false")
        ),
        sa.Column(
            "usage_count", sa.Integer(), nullable=True, server_default=sa.text("0")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create personal_space_block_attachments table
    op.create_table(
        "personal_space_block_attachments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("block_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(
            ["block_id"], ["personal_space_blocks.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create personal_space_analytics_events table
    op.create_table(
        "personal_space_analytics_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column(
            "event_data",
            sa.JSON(),
            nullable=True,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for analytics
    op.create_index(
        "idx_personal_space_analytics_user_id",
        "personal_space_analytics_events",
        ["user_id"],
    )
    op.create_index(
        "idx_personal_space_analytics_event_type",
        "personal_space_analytics_events",
        ["event_type"],
    )
    op.create_index(
        "idx_personal_space_analytics_created_at",
        "personal_space_analytics_events",
        ["created_at"],
    )

    # Insert initial template data
    op.execute(
        """
        INSERT INTO personal_space_templates (name, description, template_data, category, is_public) VALUES
        ('Tarea Básica', 'Plantilla simple para tareas', '{"type": "tarea", "metadata": {"priority": "media"}}', 'productividad', true),
        ('Nota de Estudio', 'Plantilla para notas académicas', '{"type": "nota", "metadata": {"category": "estudio", "tags": []}}', 'académico', true),
        ('Objetivo SMART', 'Plantilla para objetivos específicos', '{"type": "objetivo", "metadata": {"smart_criteria": {"specific": "", "measurable": "", "achievable": "", "relevant": "", "time_bound": ""}}}', 'metas', true),
        ('Kanban Personal', 'Tablero kanban para organización personal', '{"type": "kanban", "metadata": {"columns": ["Por hacer", "En progreso", "Completado"]}}', 'productividad', true),
        ('Lista de Verificación', 'Lista simple de tareas por completar', '{"type": "lista", "metadata": {"items": [], "allow_reorder": true}}', 'organización', true)
    """
    )


def downgrade():
    # Drop indexes and tables in reverse order

    # Analytics table indexes and table
    op.drop_index(
        "idx_personal_space_analytics_created_at",
        table_name="personal_space_analytics_events",
    )
    op.drop_index(
        "idx_personal_space_analytics_event_type",
        table_name="personal_space_analytics_events",
    )
    op.drop_index(
        "idx_personal_space_analytics_user_id",
        table_name="personal_space_analytics_events",
    )
    op.drop_table("personal_space_analytics_events")

    # Attachments table
    op.drop_table("personal_space_block_attachments")

    # Templates table
    op.drop_table("personal_space_templates")

    # Block indexes and table
    op.drop_index(
        "idx_personal_space_blocks_metadata", table_name="personal_space_blocks"
    )
    op.drop_index(
        "idx_personal_space_blocks_updated_at", table_name="personal_space_blocks"
    )
    op.drop_index("idx_personal_space_blocks_order", table_name="personal_space_blocks")
    op.drop_index(
        "idx_personal_space_blocks_status", table_name="personal_space_blocks"
    )
    op.drop_index("idx_personal_space_blocks_type", table_name="personal_space_blocks")
    op.drop_index(
        "idx_personal_space_blocks_user_id", table_name="personal_space_blocks"
    )
    op.drop_table("personal_space_blocks")
