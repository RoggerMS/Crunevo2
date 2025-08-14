#!/usr/bin/env python3
"""
Script para verificar el estado actual de la tabla user
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crunevo.app import create_app
from crunevo.extensions import db
from sqlalchemy import text

def check_user_table():
    """Verificar el estado actual de la tabla user"""
    print("🔍 VERIFICANDO TABLA USER")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Obtener información de la tabla usando PRAGMA (SQLite)
            result = db.session.execute(text("PRAGMA table_info(user)"))
            columns = result.fetchall()
            
            print("📋 Columnas en la tabla user:")
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
            
            column_names = [col[1] for col in columns]
            
            # Verificar columnas requeridas
            required_columns = [
                'id', 'username', 'email', 'password_hash', 'role', 'points', 'credits',
                'chat_enabled', 'activated', 'verification_level', 'avatar_url', 'about',
                'career', 'interests', 'mostrar_tienda_perfil', 'forum_level',
                'forum_experience', 'forum_streak', 'last_activity_date', 'questions_asked',
                'answers_given', 'best_answers', 'helpful_votes', 'reputation_score',
                'custom_forum_title'
            ]
            
            missing = [col for col in required_columns if col not in column_names]
            
            if missing:
                print(f"\n❌ Columnas faltantes: {missing}")
                return False, missing
            else:
                print("\n✅ Todas las columnas están presentes")
                return True, []
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False, []

def create_user_table_from_scratch():
    """Recrear la tabla user desde cero si es necesario"""
    print("\n🔨 RECREANDO TABLA USER")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Hacer backup de datos existentes
            print("📦 Haciendo backup de usuarios existentes...")
            backup_result = db.session.execute(text("SELECT * FROM user"))
            existing_users = backup_result.fetchall()
            print(f"📊 {len(existing_users)} usuarios encontrados")
            
            # Eliminar tabla existente
            print("🗑️ Eliminando tabla user existente...")
            db.session.execute(text("DROP TABLE IF EXISTS user"))
            
            # Crear nueva tabla con todas las columnas
            create_sql = """
            CREATE TABLE user (
                id INTEGER PRIMARY KEY,
                username VARCHAR(64) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role VARCHAR(20) DEFAULT 'student',
                points INTEGER DEFAULT 0,
                credits INTEGER DEFAULT 0,
                chat_enabled BOOLEAN DEFAULT 1,
                activated BOOLEAN DEFAULT 0,
                verification_level SMALLINT DEFAULT 0,
                avatar_url VARCHAR(255) DEFAULT 'https://res.cloudinary.com/dnp9trhfx/image/upload/v1750458582/avatar_h8okpo.png',
                about TEXT,
                career VARCHAR(120),
                interests TEXT,
                mostrar_tienda_perfil BOOLEAN DEFAULT 0,
                forum_level INTEGER DEFAULT 1,
                forum_experience INTEGER DEFAULT 0,
                forum_streak INTEGER DEFAULT 0,
                last_activity_date DATE,
                questions_asked INTEGER DEFAULT 0,
                answers_given INTEGER DEFAULT 0,
                best_answers INTEGER DEFAULT 0,
                helpful_votes INTEGER DEFAULT 0,
                reputation_score INTEGER DEFAULT 0,
                custom_forum_title VARCHAR(50)
            )
            """
            
            print("🔨 Creando nueva tabla user...")
            db.session.execute(text(create_sql))
            
            # Restaurar datos básicos
            if existing_users:
                print("📥 Restaurando usuarios básicos...")
                for user in existing_users:
                    # Solo restaurar columnas básicas que existían
                    insert_sql = """
                    INSERT INTO user (id, username, email, password_hash, role, points, credits, 
                                    chat_enabled, activated, verification_level, avatar_url, about, 
                                    career, interests, mostrar_tienda_perfil)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    
                    # Mapear valores existentes
                    values = [
                        user[0],  # id
                        user[1],  # username
                        user[2],  # email
                        user[3],  # password_hash
                        user[4] if len(user) > 4 else 'student',  # role
                        user[5] if len(user) > 5 else 0,  # points
                        user[6] if len(user) > 6 else 0,  # credits
                        user[7] if len(user) > 7 else 1,  # chat_enabled
                        user[8] if len(user) > 8 else 0,  # activated
                        user[9] if len(user) > 9 else 0,  # verification_level
                        user[10] if len(user) > 10 else 'https://res.cloudinary.com/dnp9trhfx/image/upload/v1750458582/avatar_h8okpo.png',  # avatar_url
                        user[11] if len(user) > 11 else None,  # about
                        user[12] if len(user) > 12 else None,  # career
                        user[13] if len(user) > 13 else None,  # interests
                        user[14] if len(user) > 14 else 0,  # mostrar_tienda_perfil
                    ]
                    
                    db.session.execute(text(insert_sql), values)
            
            # Crear usuario de prueba si no existe
            test_user_sql = """
            INSERT OR IGNORE INTO user (username, email, password_hash, activated)
            VALUES ('testuser', 'test@crunevo.com', 'test_hash', 1)
            """
            db.session.execute(text(test_user_sql))
            
            db.session.commit()
            print("✅ Tabla user recreada exitosamente")
            
            return True
            
        except Exception as e:
            print(f"❌ Error recreando tabla: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("VERIFICACIÓN Y CORRECCIÓN DE TABLA USER\n")
    
    # Verificar estado actual
    table_ok, missing = check_user_table()
    
    if not table_ok:
        print(f"\n⚠️ Tabla incompleta. Faltantes: {missing}")
        print("\n🔧 Procediendo a recrear la tabla...")
        
        if create_user_table_from_scratch():
            print("\n🔍 Verificando tabla recreada...")
            table_ok, missing = check_user_table()
            
            if table_ok:
                print("\n🎉 ¡TABLA USER CORREGIDA EXITOSAMENTE!")
                print("\n💡 Ahora puedes ejecutar test_block_creation_direct.py")
            else:
                print(f"\n❌ Aún hay problemas: {missing}")
        else:
            print("\n❌ Error recreando la tabla")
    else:
        print("\n✅ Tabla user está correcta")