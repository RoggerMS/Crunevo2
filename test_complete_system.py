#!/usr/bin/env python3
"""
Prueba completa del sistema Personal Space
Verifica que todas las funcionalidades críticas estén funcionando correctamente.
"""

import requests
import json
from bs4 import BeautifulSoup

def test_complete_system():
    """Prueba completa del sistema Personal Space."""
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    print("=== Prueba Completa del Sistema Personal Space ===")
    print()
    
    try:
        # 1. Obtener token CSRF
        print("1. Obteniendo token CSRF...")
        login_page = session.get(f"{base_url}/login")
        if login_page.status_code != 200:
            print(f"❌ Error al acceder a la página de login: {login_page.status_code}")
            return False
            
        soup = BeautifulSoup(login_page.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})['value']
        print(f"✅ Token CSRF obtenido: {csrf_token[:20]}...")
        
        # 2. Realizar login
        print("\n2. Realizando login...")
        login_data = {
            "username": "testadmin",
            "password": "admin123",
            "csrf_token": csrf_token
        }
        
        login_response = session.post(
            f"{base_url}/login",
            data=login_data,
            headers={"X-CSRFToken": csrf_token},
            allow_redirects=False
        )
        
        if login_response.status_code not in [200, 302]:
            print(f"❌ Error en login: {login_response.status_code}")
            return False
        print("✅ Login exitoso")
        
        # 3. Acceder a Personal Space
        print("\n3. Accediendo a Personal Space...")
        ps_response = session.get(f"{base_url}/personal-space")
        if ps_response.status_code != 200:
            print(f"❌ Error al acceder a Personal Space: {ps_response.status_code}")
            return False
        print("✅ Acceso a Personal Space exitoso")
        
        # 4. Obtener nuevo token CSRF para API
        soup = BeautifulSoup(ps_response.text, 'html.parser')
        csrf_meta = soup.find('meta', {'name': 'csrf-token'})
        if csrf_meta:
            new_csrf_token = csrf_meta['content']
        else:
            new_csrf_token = csrf_token
        
        # 5. Crear un bloque de prueba
        print("\n4. Creando bloque de prueba...")
        block_data = {
            "title": "Bloque de Prueba Sistema",
            "description": "Este es un bloque creado para probar el sistema completo",
            "type": "nota",
            "category": "personal",
            "priority": "medium",
            "theme_color": "blue"
        }
        
        create_response = session.post(
            f"{base_url}/api/personal-space/blocks",
            json=block_data,
            headers={
                "X-CSRFToken": new_csrf_token,
                "Content-Type": "application/json"
            }
        )
        
        if create_response.status_code in [200, 201]:
            block_result = create_response.json()
            if block_result.get('success', True):
                block_id = block_result.get('block', {}).get('id')
                print(f"✅ Bloque creado exitosamente: {block_id}")
            else:
                print(f"❌ Error al crear bloque: {block_result.get('error', 'Error desconocido')}")
                return False
        else:
            print(f"❌ Error al crear bloque: {create_response.status_code}")
            print(f"Respuesta: {create_response.text[:200]}...")
            return False
        
        # 6. Listar bloques
        print("\n5. Listando bloques...")
        list_response = session.get(
            f"{base_url}/api/personal-space/blocks",
            headers={"X-CSRFToken": new_csrf_token}
        )
        
        if list_response.status_code == 200:
            blocks_data = list_response.json()
            blocks_count = len(blocks_data.get('blocks', []))
            print(f"✅ Bloques listados exitosamente: {blocks_count} bloques encontrados")
        else:
            print(f"❌ Error al listar bloques: {list_response.status_code}")
            return False
        
        # 7. Probar Analytics
        print("\n6. Probando Analytics...")
        analytics_response = session.get(
            f"{base_url}/api/personal-space/analytics/dashboard",
            headers={"X-CSRFToken": new_csrf_token}
        )
        
        if analytics_response.status_code == 200:
            analytics_data = analytics_response.json()
            print("✅ Analytics funcionando correctamente")
        else:
            print(f"❌ Error en Analytics: {analytics_response.status_code}")
            return False
        
        # 8. Probar página de Analytics
        print("\n7. Probando página de Analytics...")
        analytics_page = session.get(f"{base_url}/personal-space/analytics")
        if analytics_page.status_code == 200:
            print("✅ Página de Analytics accesible")
        else:
            print(f"❌ Error en página de Analytics: {analytics_page.status_code}")
            return False
        
        # 9. Probar página de Configuración
        print("\n8. Probando página de Configuración...")
        config_page = session.get(f"{base_url}/personal-space/configuracion")
        if config_page.status_code == 200:
            print("✅ Página de Configuración accesible")
        else:
            print(f"❌ Error en página de Configuración: {config_page.status_code}")
            return False
        
        print("\n🎉 ¡Todas las pruebas del sistema pasaron exitosamente!")
        print("\n📊 Resumen de funcionalidades verificadas:")
        print("   ✅ Autenticación de usuarios")
        print("   ✅ Acceso a Personal Space")
        print("   ✅ Creación de bloques")
        print("   ✅ Listado de bloques")
        print("   ✅ API de Analytics")
        print("   ✅ Página de Analytics")
        print("   ✅ Página de Configuración")
        
        return True
        
    except Exception as e:
        print(f"💥 Error durante las pruebas: {e}")
        return False

if __name__ == "__main__":
    success = test_complete_system()
    if not success:
        print("\n💥 Las pruebas fallaron. Revisar los errores anteriores.")
        exit(1)
    else:
        print("\n✨ Sistema Personal Space funcionando perfectamente.")