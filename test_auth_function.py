#!/usr/bin/env python3
"""
Script para probar directamente la función authenticate_user
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crunevo import create_app
from crunevo.services.auth_service import authenticate_user
from crunevo.extensions import db
from crunevo.models import User

def test_authenticate_function():
    """Test authenticate_user function directly"""
    app = create_app()
    
    with app.app_context():
        print("🧪 TESTING AUTHENTICATE_USER FUNCTION")
        print("=" * 50)
        
        try:
            # Test with valid user
            print("1. 🔍 Buscando usuario testuser...")
            user = User.query.filter_by(username='testuser').first()
            if user:
                print(f"   ✅ Usuario encontrado: {user.username}")
                print(f"   Activado: {user.activated}")
                print(f"   Email: {user.email}")
            else:
                print("   ❌ Usuario no encontrado")
                return
                
            print("\n2. 🔐 Probando authenticate_user...")
            result = authenticate_user('testuser', 'testpass123')
            print(f"   Resultado: {result}")
            
            user_result, error, wait = result
            if user_result:
                print(f"   ✅ Autenticación exitosa: {user_result.username}")
            else:
                print(f"   ❌ Error de autenticación: {error}, wait: {wait}")
                
            print("\n3. 🔐 Probando con credenciales incorrectas...")
            result2 = authenticate_user('testuser', 'wrongpass')
            user_result2, error2, wait2 = result2
            print(f"   Resultado: user={user_result2}, error={error2}, wait={wait2}")
            
        except Exception as e:
            print(f"❌ Error en test: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_authenticate_function()