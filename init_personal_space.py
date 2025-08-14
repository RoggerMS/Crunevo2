#!/usr/bin/env python3
"""
Script para inicializar las tablas de Personal Space si no existen.
Este script verifica y crea las tablas necesarias para el funcionamiento del sistema.
"""

from crunevo import create_app
from crunevo.extensions import db
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_table_exists(table_name: str) -> bool:
    """Verificar si una tabla existe en la base de datos."""
    try:
        inspector = inspect(db.engine)
        return inspector.has_table(table_name)
    except SQLAlchemyError as e:
        logger.error(f"Error checking table {table_name}: {e}")
        return False

def create_personal_space_blocks_table():
    """Crear la tabla personal_space_blocks si no existe."""
    if check_table_exists('personal_space_blocks'):
        logger.info("Tabla personal_space_blocks ya existe")
        return True
    
    try:
        logger.info("Creando tabla personal_space_blocks...")
        
        # SQL para crear la tabla personal_space_blocks
        create_table_sql = """
        CREATE TABLE personal_space_blocks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id INTEGER NOT NULL,
            type VARCHAR(50) NOT NULL,
            title VARCHAR(255) NOT NULL,
            content TEXT,
            metadata JSON DEFAULT '{}',
            order_index INTEGER DEFAULT 0,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            CONSTRAINT check_block_type CHECK (type IN (
                'tarea', 'nota', 'kanban', 'objetivo', 'bitacora', 'enlace', 
                'frase', 'recordatorio', 'meta', 'lista', 'nota_enriquecida', 
                'bloque_personalizado'
            )),
            CONSTRAINT check_block_status CHECK (status IN (
                'active', 'completed', 'archived', 'deleted'
            )),
            CONSTRAINT fk_personal_space_blocks_user_id 
                FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
        );
        """
        
        db.session.execute(text(create_table_sql))
        
        # Crear índices
        indices_sql = [
            "CREATE INDEX idx_personal_space_blocks_user_id ON personal_space_blocks(user_id);",
            "CREATE INDEX idx_personal_space_blocks_type ON personal_space_blocks(type);",
            "CREATE INDEX idx_personal_space_blocks_status ON personal_space_blocks(status);",
            "CREATE INDEX idx_personal_space_blocks_order ON personal_space_blocks(user_id, order_index);",
            "CREATE INDEX idx_personal_space_blocks_updated_at ON personal_space_blocks(updated_at DESC);",
            "CREATE INDEX idx_personal_space_blocks_metadata ON personal_space_blocks USING GIN(metadata);"
        ]
        
        for index_sql in indices_sql:
            try:
                db.session.execute(text(index_sql))
            except SQLAlchemyError as e:
                logger.warning(f"Error creando índice: {e}")
        
        db.session.commit()
        logger.info("Tabla personal_space_blocks creada exitosamente")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Error creando tabla personal_space_blocks: {e}")
        db.session.rollback()
        return False

def create_personal_space_templates_table():
    """Crear la tabla personal_space_templates si no existe."""
    if check_table_exists('personal_space_templates'):
        logger.info("Tabla personal_space_templates ya existe")
        return True
    
    try:
        logger.info("Creando tabla personal_space_templates...")
        
        create_table_sql = """
        CREATE TABLE personal_space_templates (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id INTEGER,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            template_data JSON NOT NULL,
            category VARCHAR(100),
            is_public BOOLEAN DEFAULT false,
            usage_count INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            CONSTRAINT fk_personal_space_templates_user_id 
                FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
        );
        """
        
        db.session.execute(text(create_table_sql))
        
        # Insertar plantillas por defecto
        default_templates_sql = """
        INSERT INTO personal_space_templates (name, description, template_data, category, is_public) VALUES
        ('Tarea Básica', 'Plantilla simple para tareas', '{"type": "tarea", "metadata": {"priority": "medium"}}', 'productividad', true),
        ('Nota de Estudio', 'Plantilla para notas académicas', '{"type": "nota", "metadata": {"category": "estudio", "tags": []}}', 'académico', true),
        ('Objetivo SMART', 'Plantilla para objetivos específicos', '{"type": "objetivo", "metadata": {"progress": 0, "status": "no_iniciada"}}', 'metas', true),
        ('Kanban Personal', 'Tablero kanban para organización personal', '{"type": "kanban", "metadata": {"columns": {"por_hacer": [], "en_progreso": [], "hecho": []}}}', 'productividad', true),
        ('Lista de Verificación', 'Lista simple de tareas por completar', '{"type": "lista", "metadata": {"tasks": []}}', 'organización', true);
        """
        
        db.session.execute(text(default_templates_sql))
        db.session.commit()
        logger.info("Tabla personal_space_templates creada exitosamente")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Error creando tabla personal_space_templates: {e}")
        db.session.rollback()
        return False

def create_personal_space_analytics_events_table():
    """Crear la tabla personal_space_analytics_events si no existe."""
    if check_table_exists('personal_space_analytics_events'):
        logger.info("Tabla personal_space_analytics_events ya existe")
        return True
    
    try:
        logger.info("Creando tabla personal_space_analytics_events...")
        
        create_table_sql = """
        CREATE TABLE personal_space_analytics_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id INTEGER NOT NULL,
            event_type VARCHAR(100) NOT NULL,
            event_data JSON DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            CONSTRAINT fk_personal_space_analytics_user_id 
                FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
        );
        """
        
        db.session.execute(text(create_table_sql))
        
        # Crear índices
        indices_sql = [
            "CREATE INDEX idx_personal_space_analytics_user_id ON personal_space_analytics_events(user_id);",
            "CREATE INDEX idx_personal_space_analytics_event_type ON personal_space_analytics_events(event_type);",
            "CREATE INDEX idx_personal_space_analytics_created_at ON personal_space_analytics_events(created_at);"
        ]
        
        for index_sql in indices_sql:
            try:
                db.session.execute(text(index_sql))
            except SQLAlchemyError as e:
                logger.warning(f"Error creando índice: {e}")
        
        db.session.commit()
        logger.info("Tabla personal_space_analytics_events creada exitosamente")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Error creando tabla personal_space_analytics_events: {e}")
        db.session.rollback()
        return False

def init_personal_space_tables():
    """Inicializar todas las tablas de Personal Space."""
    logger.info("Iniciando verificación e inicialización de tablas Personal Space...")
    
    success = True
    
    # Crear tablas en orden de dependencias
    if not create_personal_space_blocks_table():
        success = False
    
    if not create_personal_space_templates_table():
        success = False
    
    if not create_personal_space_analytics_events_table():
        success = False
    
    if success:
        logger.info("✅ Todas las tablas de Personal Space están listas")
    else:
        logger.error("❌ Hubo errores al crear algunas tablas")
    
    return success

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        print("🚀 Inicializando Personal Space...")
        
        # Verificar conexión a la base de datos
        try:
            db.session.execute(text("SELECT 1"))
            print("✅ Conexión a la base de datos exitosa")
        except SQLAlchemyError as e:
            print(f"❌ Error de conexión a la base de datos: {e}")
            exit(1)
        
        # Inicializar tablas
        if init_personal_space_tables():
            print("🎉 Personal Space inicializado correctamente")
        else:
            print("⚠️ Personal Space inicializado con algunos