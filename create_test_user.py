#!/usr/bin/env python3
"""
Script para crear un usuario de prueba para testing
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crunevo.app import create_app
from crunevo.extensions import db
from crunevo.models.user import User
from sqlalchemy import text

def create_test_user():
    """Crear usuario de prueba para testing"""
    print("🔧 CREANDO USUARIO DE PRUEBA")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Verificar si ya existe
            existing_user = User.query.filter_by(username='testadmin').first()
            if existing_user:
                print("✅ Usuario testadmin ya existe")
                print(f"   - Username: {existing_user.username}")
                print(f"   - Email: {existing_user.email}")
                print(f"   - Role: {existing_user.role}")
                print(f"   - Activated: {existing_user.activated}")
                return True
            
            # Crear nuevo usuario
            print("📝 Creando nuevo usuario testadmin...")
            user = User(
                username='testadmin',
                email='testadmin@crunevo.com',
                role='admin',
                activated=True,
                points=100,
                credits=50
            )
            user.set_password('admin123')
            
            db.session.add(user)
            db.session.commit()
            
            print("✅ Usuario testadmin creado exitosamente")
            print("   - Username: testadmin")
            print("   - Password: admin123")
            print("   - Email: testadmin@crunevo.com")
            print("   - Role: admin")
            print("   - Activated: True")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creando usuario: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False

def list_existing_users():
    """Listar usuarios existentes"""
    print("\n👥 USUARIOS EXISTENTES")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        try:
            users = User.query.all()
            if not users:
                print("❌ No hay usuarios en la base de datos")
                return
            
            for user in users:
                print(f"   - {user.username} ({user.email}) - Role: {user.role} - Activated: {user.activated}")
                
        except Exception as e:
            print(f"❌ Error listando usuarios: {e}")

if __name__ == "__main__":
    print("CREACIÓN DE USUARIO DE PRUEBA\n")
    
    # Listar usuarios existentes
    list_existing_users()
    
    # Crear usuario de prueba
    if create_test_user():
        print("\n🎉 ¡USUARIO DE PRUEBA LISTO!")
        print("\n💡 Credenciales para testing:")
        print("   - Username: testadmin")
        print("   - Password: admin123")
    else:
        print("\n❌ Error creando usuario de prueba")