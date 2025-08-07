#!/usr/bin/env python3
"""
Script de diagnóstico para producción en Fly.io
Este script verifica la configuración y estado de la aplicación.
"""

import os
import sys
from flask import Flask
from crunevo.config import Config

def check_environment():
    """Verifica las variables de entorno críticas"""
    print("=== VERIFICACIÓN DE ENTORNO ===")
    
    critical_vars = [
        'FLASK_ENV',
        'FLASK_DEBUG', 
        'SECRET_KEY',
        'DATABASE_URL',
        'PORT'
    ]
    
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            # Ocultar valores sensibles
            if var in ['SECRET_KEY', 'DATABASE_URL']:
                display_value = f"{value[:10]}..." if len(value) > 10 else "***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NO CONFIGURADA")
    
    print()

def check_config():
    """Verifica la configuración de Flask"""
    print("=== CONFIGURACIÓN DE FLASK ===")
    
    config = Config()
    
    print(f"DEBUG: {config.DEBUG}")
    print(f"FLASK_ENV: {config.FLASK_ENV}")
    print(f"IS_PRODUCTION: {config.IS_PRODUCTION}")
    print(f"SESSION_COOKIE_SECURE: {config.SESSION_COOKIE_SECURE}")
    print(f"SESSION_COOKIE_SAMESITE: {config.SESSION_COOKIE_SAMESITE}")
    
    # Verificar base de datos
    db_uri = config.SQLALCHEMY_DATABASE_URI
    if db_uri.startswith('postgresql'):
        print("✅ Base de datos: PostgreSQL")
    elif db_uri.startswith('sqlite'):
        print("⚠️  Base de datos: SQLite (desarrollo)")
    else:
        print(f"❓ Base de datos: {db_uri[:20]}...")
    
    print()

def check_app_creation():
    """Intenta crear la aplicación Flask"""
    print("=== CREACIÓN DE APLICACIÓN ===")
    
    try:
        from crunevo.app import create_app
        app = create_app()
        print("✅ Aplicación Flask creada exitosamente")
        
        # Verificar configuración de la app
        with app.app_context():
            print(f"✅ Contexto de aplicación: OK")
            print(f"✅ Configuración cargada: {len(app.config)} variables")
            
            # Verificar base de datos
            try:
                from crunevo.extensions import db
                # Intentar una consulta simple
                db.engine.execute('SELECT 1')
                print("✅ Conexión a base de datos: OK")
            except Exception as e:
                print(f"❌ Error de base de datos: {e}")
                
    except Exception as e:
        print(f"❌ Error creando aplicación: {e}")
        import traceback
        traceback.print_exc()
    
    print()

def check_user_loader():
    """Verifica el user loader de Flask-Login"""
    print("=== VERIFICACIÓN DE USER LOADER ===")
    
    try:
        from crunevo.app import create_app
        from crunevo.models.user import User
        
        app = create_app()
        with app.app_context():
            # Buscar usuario estudiante
            user = User.query.filter_by(username='estudiante').first()
            if user:
                print(f"✅ Usuario 'estudiante' encontrado (ID: {user.id})")
                print(f"   Email: {user.email}")
                print(f"   Activado: {user.activated}")
                print(f"   Rol: {user.role}")
            else:
                print("❌ Usuario 'estudiante' no encontrado")
                
    except Exception as e:
        print(f"❌ Error verificando usuario: {e}")
    
    print()

def main():
    """Función principal"""
    print("🔍 DIAGNÓSTICO DE PRODUCCIÓN - CRUNEVO")
    print("=" * 50)
    print()
    
    check_environment()
    check_config()
    check_app_creation()
    check_user_loader()
    
    print("🏁 Diagnóstico completado")

if __name__ == '__main__':
    main()