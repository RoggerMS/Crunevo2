#!/usr/bin/env python3
"""
Script para probar la creación de bloques después de las correcciones realizadas.
"""

import requests
import re
from bs4 import BeautifulSoup

def test_block_creation():
    base_url = 'http://localhost:5000'
    session = requests.Session()
    
    print("=== Prueba de Creación de Bloques (Post-Fix) ===")
    
    try:
        # 1. Obtener token CSRF del login
        print("\n1. Obteniendo token CSRF...")
        login_response = session.get(f'{base_url}/login')
        if login_response.status_code != 200:
            print(f"❌ Error al acceder a login: {login_response.status_code}")
            return False
            
        soup = BeautifulSoup(login_response.text, 'html.parser')
        csrf_token = None
        csrf_input = soup.find('input', {'name': 'csrf_token'})
        if csrf_input:
            csrf_token = csrf_input.get('value')
        
        if not csrf_token:
            csrf_match = re.search(r'csrf_token["\']\s*:\s*["\']([^"\'\']+)["\']', login_response.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)
        
        if not csrf_token:
            print("❌ No se pudo obtener el token CSRF")
            return False
            
        print(f"✅ Token CSRF obtenido: {csrf_token[:20]}...")
        
        # 2. Realizar login
        print("\n2. Realizando login...")
        login_data = {
            'username': 'testadmin',
            'password': 'admin123',
            'csrf_token': csrf_token
        }
        
        login_post = session.post(
            f'{base_url}/login',
            data=login_data,
            headers={'X-CSRFToken': csrf_token},
            allow_redirects=False  # No seguir redirects automáticamente
        )
        print(f"Login response: {login_post.status_code}")
        print(f"Login cookies: {dict(session.cookies)}")
        
        # Un 302 indica login exitoso
        if login_post.status_code not in [200, 302]:
            print(f"❌ Error en login: {login_post.status_code}")
            print(f"Respuesta: {login_post.text[:200]}...")
            return False
            
        print("✅ Login exitoso")
        
        # 3. Acceder directamente a personal-space
        print("\n3. Accediendo a personal-space...")
        ps_response = session.get(f'{base_url}/personal-space')
        if ps_response.status_code != 200:
            print(f"❌ Error al acceder a personal-space: {ps_response.status_code}")
            return False
            
        print("✅ Acceso a personal-space exitoso")
        
        # 4. Extraer nuevo token CSRF de la página
        soup = BeautifulSoup(ps_response.text, 'html.parser')
        new_csrf_token = None
        
        # Buscar en meta tags
        csrf_meta = soup.find('meta', {'name': 'csrf-token'})
        if csrf_meta:
            new_csrf_token = csrf_meta.get('content')
        
        # Buscar en scripts
        if not new_csrf_token:
            csrf_match = re.search(r'csrf_token["\']\s*:\s*["\']([^"\'\']+)["\']', ps_response.text)
            if csrf_match:
                new_csrf_token = csrf_match.group(1)
        
        if new_csrf_token:
            csrf_token = new_csrf_token
            print(f"✅ Nuevo token CSRF obtenido: {csrf_token[:20]}...")
        
        # 5. Probar creación de bloque
        print("\n4. Probando creación de bloque...")
        block_data = {
            'type': 'nota',
            'title': 'Prueba Post-Fix',
            'content': 'Este es un bloque de prueba creado después de las correcciones.',
            'metadata': {
                'color': 'blue',
                'icon': 'bi-journal-text'
            }
        }
        
        print(f"URL de creación: {base_url}/api/personal-space/blocks")
        print(f"CSRF Token: {new_csrf_token[:20]}...")
        
        headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token
        }
        
        create_response = session.post(
            f'{base_url}/api/personal-space/blocks',
            json=block_data,
            headers=headers
        )
        
        print(f"Respuesta de creación: {create_response.status_code}")
        print(f"Headers de respuesta: {dict(create_response.headers)}")
        
        if create_response.status_code == 200:
            try:
                response_data = create_response.json()
                if response_data.get('success'):
                    print("✅ ¡Bloque creado exitosamente!")
                    print(f"ID del bloque: {response_data.get('block', {}).get('id')}")
                    return True
                else:
                    print(f"❌ Error en la respuesta: {response_data.get('message', 'Error desconocido')}")
                    return False
            except Exception as e:
                print(f"❌ Error al parsear JSON: {e}")
                print(f"Respuesta raw: {create_response.text[:500]}")
                print(f"URL final: {create_response.url}")
                return False
        else:
            print(f"❌ Error HTTP: {create_response.status_code}")
            print(f"Respuesta: {create_response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

if __name__ == '__main__':
    success = test_block_creation()
    if success:
        print("\n🎉 ¡Todas las pruebas pasaron! La creación de bloques funciona correctamente.")
    else:
        print("\n💥 Las pruebas fallaron. Revisar los errores anteriores.")