"""Migrate Personal Space Data to New Schema

Revision ID: migrate_personal_space_data
Revises: personal_space_redesign_schema
Create Date: 2024-01-15 10:30:00.000000

"""

from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "migrate_personal_space_data"
down_revision = "personal_space_redesign_schema"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    if connection.dialect.name == "sqlite":
        return

    # Create temporary table for migration mapping
    op.execute(
        """
        CREATE TEMP TABLE block_migration_map (
            old_id INTEGER,
            new_id UUID,
            migration_status VARCHAR(20)
        )
    """
    )

    # Check if old personal space tables exist and migrate data
    inspector = inspect(connection)
    old_table_exists = "block" in inspector.get_table_names()

    if old_table_exists:
        # Migrate existing blocks to new structure
        op.execute(
            """
            INSERT INTO personal_space_blocks (id, user_id, type, title, content, metadata, order_index, status, created_at, updated_at)
            SELECT 
                gen_random_uuid() as id,
                user_id,
                type,
                COALESCE(title, 'Sin título') as title,
                content,
                CASE 
                    WHEN metadata IS NOT NULL THEN metadata::jsonb
                    ELSE '{}'::jsonb
                END as metadata,
                COALESCE(order_index, 0) as order_index,
                CASE 
                    WHEN status IS NULL THEN 'active'
                    WHEN status = 'deleted' THEN 'deleted'
                    WHEN status = 'completed' THEN 'completed'
                    ELSE 'active'
                END as status,
                COALESCE(created_at, NOW()) as created_at,
                COALESCE(updated_at, NOW()) as updated_at
            FROM block
            WHERE deleted_at IS NULL OR deleted_at IS NOT NULL
        """
        )

        # Record migration mapping
        op.execute(
            """
            INSERT INTO block_migration_map (old_id, new_id, migration_status)
            SELECT 
                ob.id as old_id,
                nb.id as new_id,
                'migrated' as migration_status
            FROM block ob
            JOIN personal_space_blocks nb ON ob.user_id = nb.user_id 
                AND COALESCE(ob.title, 'Sin título') = nb.title
                AND ob.type = nb.type
        """
        )

        # Update metadata with migration information
        op.execute(
            """
            UPDATE personal_space_blocks 
            SET metadata = metadata || jsonb_build_object(
                'migrated_from', 'legacy_system',
                'migration_date', NOW()::text,
                'legacy_id', (
                    SELECT old_id::text 
                    FROM block_migration_map 
                    WHERE new_id = personal_space_blocks.id
                )
            )
            WHERE id IN (SELECT new_id FROM block_migration_map)
        """
        )

    # Create additional templates based on popular block types
    op.execute(
        """
        INSERT INTO personal_space_templates (name, description, template_data, category, is_public)
        SELECT 
            'Plantilla ' || type || ' Popular' as name,
            'Generada automáticamente desde bloques populares' as description,
            jsonb_build_object(
                'type', type,
                'metadata', jsonb_build_object(
                    'template_source', 'auto_generated',
                    'based_on_usage', 'true'
                )
            ) as template_data,
            'auto_generated' as category,
            true as is_public
        FROM (
            SELECT type, COUNT(*) as usage_count
            FROM personal_space_blocks 
            GROUP BY type
            HAVING COUNT(*) > 5
        ) popular_types
        WHERE NOT EXISTS (
            SELECT 1 FROM personal_space_templates 
            WHERE name = 'Plantilla ' || popular_types.type || ' Popular'
        )
    """
    )

    # Create analytics events for existing blocks
    op.execute(
        """
        INSERT INTO personal_space_analytics_events (user_id, event_type, event_data)
        SELECT 
            user_id,
            'block_migrated' as event_type,
            jsonb_build_object(
                'block_type', type,
                'migration_date', NOW()::text,
                'source', 'legacy_migration'
            ) as event_data
        FROM personal_space_blocks
        WHERE metadata->>'migrated_from' = 'legacy_system'
    """
    )


def downgrade():
    # Remove migrated data (be careful with this in production)
    op.execute(
        """
        DELETE FROM personal_space_analytics_events 
        WHERE event_type = 'block_migrated'
    """
    )

    op.execute(
        """
        DELETE FROM personal_space_templates 
        WHERE category = 'auto_generated'
    """
    )

    op.execute(
        """
        DELETE FROM personal_space_blocks 
        WHERE metadata->>'migrated_from' = 'legacy_system'
    """
    )
