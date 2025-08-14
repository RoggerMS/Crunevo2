#!/usr/bin/env python3
"""
Script para corregir la tabla user agregando las columnas faltantes
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crunevo.app import create_app
from crunevo.extensions import db
from sqlalchemy import text
from sqlalchemy.engine.reflection import Inspector

def fix_user_table():
    """Agregar columnas faltantes a la tabla user"""
    print("🔧 CORRIGIENDO TABLA USER")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Obtener inspector para verificar columnas existentes
            inspector = Inspector.from_engine(db.engine)
            
            # Verificar si la tabla existe
            if not inspector.has_table('user'):
                print("❌ Tabla 'user' no existe")
                return False
            
            # Obtener columnas existentes
            existing_columns = [col['name'] for col in inspector.get_columns('user')]
            print(f"📋 Columnas existentes: {existing_columns}")
            
            # Definir todas las columnas que deberían existir
            required_columns = {
                'id': 'INTEGER PRIMARY KEY',
                'username': 'VARCHAR(64) UNIQUE NOT NULL',
                'email': 'VARCHAR(120) UNIQUE NOT NULL',
                'password_hash': 'TEXT NOT NULL',
                'role': 'VARCHAR(20) DEFAULT "student"',
                'points': 'INTEGER DEFAULT 0',
                'credits': 'INTEGER DEFAULT 0',
                'chat_enabled': 'BOOLEAN DEFAULT 1',
                'activated': 'BOOLEAN DEFAULT 0',
                'verification_level': 'SMALLINT DEFAULT 0',
                'avatar_url': 'VARCHAR(255) DEFAULT "https://res.cloudinary.com/dnp9trhfx/image/upload/v1750458582/avatar_h8okpo.png"',
                'about': 'TEXT',
                'career': 'VARCHAR(120)',
                'interests': 'TEXT',
                'mostrar_tienda_perfil': 'BOOLEAN DEFAULT 0',
                'forum_level': 'INTEGER DEFAULT 1',
                'forum_experience': 'INTEGER DEFAULT 0',
                'forum_streak': 'INTEGER DEFAULT 0',
                'last_activity_date': 'DATE',
                'questions_asked': 'INTEGER DEFAULT 0',
                'answers_given': 'INTEGER DEFAULT 0',
                'best_answers': 'INTEGER DEFAULT 0',
                'helpful_votes': 'INTEGER DEFAULT 0',
                'reputation_score': 'INTEGER DEFAULT 0',
                'custom_forum_title': 'VARCHAR(50)'
            }
            
            # Identificar columnas faltantes
            missing_columns = []
            for col_name, col_def in required_columns.items():
                if col_name not in existing_columns:
                    missing_columns.append((col_name, col_def))
            
            if not missing_columns:
                print("✅ Todas las columnas ya existen")
                return True
            
            print(f"🔍 Columnas faltantes: {[col[0] for col in missing_columns]}")
            
            # Agregar columnas faltantes
            for col_name, col_def in missing_columns:
                try:
                    # Construir comando ALTER TABLE
                    if 'DEFAULT' in col_def:
                        # Separar tipo y default
                        parts = col_def.split(' DEFAULT ')
                        col_type = parts[0]
                        default_value = parts[1].strip('"')
                        
                        if col_type in ['BOOLEAN', 'INTEGER', 'SMALLINT']:
                            sql = f"ALTER TABLE user ADD COLUMN {col_name} {col_type} DEFAULT {default_value}"
                        else:
                            sql = f"ALTER TABLE user ADD COLUMN {col_name} {col_type} DEFAULT '{default_value}'"
                    else:
                        sql = f"ALTER TABLE user ADD COLUMN {col_name} {col_def}"
                    
                    print(f"📝 Ejecutando: {sql}")
                    db.session.execute(text(sql))
                    db.session.commit()
                    print(f"✅ Columna '{col_name}' agregada")
                    
                except Exception as e:
                    print(f"⚠️ Error agregando columna '{col_name}': {e}")
                    db.session.rollback()
                    continue
            
            # Verificar que todas las columnas fueron agregadas
            updated_columns = [col['name'] for col in inspector.get_columns('user')]
            print(f"\n📋 Columnas después de la actualización: {updated_columns}")
            
            # Verificar columnas faltantes restantes
            still_missing = [col for col in required_columns.keys() if col not in updated_columns]
            
            if still_missing:
                print(f"⚠️ Columnas que aún faltan: {still_missing}")
                return False
            else:
                print("\n🎉 ¡Tabla user actualizada correctamente!")
                return True
                
        except Exception as e:
            print(f"❌ Error general: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_user_creation():
    """Probar la creación de un usuario después de la corrección"""
    print("\n🧪 PROBANDO CREACIÓN DE USUARIO")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        try:
            from crunevo.models import User
            
            # Verificar si el usuario de prueba ya existe
            existing_user = User.query.filter_by(email='test@crunevo.com').first()
            if existing_user:
                print(f"✅ Usuario de prueba ya existe: {existing_user.username}")
                return True
            
            # Crear usuario de prueba
            test_user = User(
                username='testuser',
                email='test@crunevo.com',
                password_hash='test_hash',
                is_activated=True
            )
            
            db.session.add(test_user)
            db.session.commit()
            
            print(f"✅ Usuario de prueba creado: {test_user.username} (ID: {test_user.id})")
            return True
            
        except Exception as e:
            print(f"❌ Error creando usuario: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("CORRECCIÓN DE TABLA USER\n")
    
    # Corregir tabla
    table_fixed = fix_user_table()
    
    if table_fixed:
        # Probar creación de usuario
        user_created = test_user_creation()
        
        if user_created:
            print("\n" + "=" * 50)
            print("✅ CORRECCIÓN COMPLETADA EXITOSAMENTE")
            print("\n💡 Ahora puedes ejecutar test_block_creation_direct.py")
            print("=" * 50)
        else:
            print("\n❌ Error en la creación de usuario")
    else:
        print("\n❌ Error corrigiendo la tabla user")