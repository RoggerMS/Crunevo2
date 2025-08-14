#!/usr/bin/env python3
"""
Script para simular exactamente lo que hace el frontend al crear bloques
y diagnosticar el problema "Error al crear el bloque"
"""

import os
import sys
import requests
import json
from urllib.parse import urljoin

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_frontend_simulation():
    """Simula exactamente lo que hace el frontend"""
    print("=== SIMULACIÓN FRONTEND ===\n")
    
    # Configurar la URL base
    base_url = "http://localhost:5000"  # Ajustar según tu configuración
    
    # Simular una sesión de navegador
    session = requests.Session()
    
    try:
        # 1. Primero obtener la página principal para conseguir el CSRF token
        print("1. Obteniendo CSRF token...")
        response = session.get(urljoin(base_url, "/personal-space"))
        
        if response.status_code != 200:
            print(f"❌ Error al acceder a personal-space: {response.status_code}")
            return False
            
        # Extraer CSRF token del HTML
        import re
        csrf_match = re.search(r'<meta name="csrf-token" content="([^"]+)"', response.text)
        if not csrf_match:
            print("❌ No se encontró el CSRF token en la página")
            return False
            
        csrf_token = csrf_match.group(1)
        print(f"✓ CSRF token obtenido: {csrf_token[:20]}...")
        
        # 2. Simular la creación de un bloque exactamente como lo hace el frontend
        print("\n2. Simulando creación de bloque...")
        
        block_data = {
            "type": "nota",
            "title": "Nueva nota",
            "content": "",
            "metadata": {
                "color": "indigo",
                "icon": "bi-card-text"
            }
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token,
            'X-Requested-With': 'XMLHttpRequest',
            'X-Device-Token': 'test-device-token'
        }
        
        print(f"Enviando datos: {json.dumps(block_data, indent=2)}")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        
        # Hacer la petición POST
        response = session.post(
            urljoin(base_url, "/api/personal-space/blocks"),
            json=block_data,
            headers=headers
        )
        
        print(f"\nRespuesta del servidor:")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"Datos de respuesta: {json.dumps(response_data, indent=2)}")
            
            if response.status_code == 200 and response_data.get('success'):
                print("\n✓ ¡Bloque creado exitosamente desde simulación frontend!")
                
                # Limpiar el bloque de prueba
                block_id = response_data.get('block', {}).get('id')
                if block_id:
                    delete_response = session.delete(
                        urljoin(base_url, f"/api/personal-space/blocks/{block_id}"),
                        headers=headers
                    )
                    print(f"Bloque de prueba eliminado: {delete_response.status_code}")
                
                return True
            else:
                print(f"\n❌ Error en la respuesta: {response_data}")
                return False
                
        except json.JSONDecodeError:
            print(f"❌ Error al decodificar JSON. Respuesta raw: {response.text[:500]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión. ¿Está el servidor ejecutándose?")
        print("   Ejecuta: python app.py")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_direct_api_call():
    """Prueba directa de la API sin simular navegador"""
    print("\n=== PRUEBA DIRECTA API ===\n")
    
    base_url = "http://localhost:5000"
    
    block_data = {
        "type": "nota",
        "title": "Nueva nota directa",
        "content": "",
        "metadata": {
            "color": "indigo",
            "icon": "bi-card-text"
        }
    }
    
    try:
        response = requests.post(
            urljoin(base_url, "/api/personal-space/blocks"),
            json=block_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Respuesta: {response.text[:500]}")
        
        if response.status_code == 403:
            print("\n✓ Error 403 esperado (falta CSRF token)")
            return True
        else:
            print(f"\n❌ Respuesta inesperada: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("DIAGNÓSTICO DE CREACIÓN DE BLOQUES - SIMULACIÓN FRONTEND\n")
    print("Este script simula exactamente lo que hace el navegador")
    print("para identificar dónde está fallando la creación de bloques.\n")
    
    # Verificar que el servidor esté ejecutándose
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        print("✓ Servidor detectado en http://localhost:5000\n")
    except:
        print("❌ No se puede conectar al servidor en http://localhost:5000")
        print("   Por favor, ejecuta: python app.py\n")
        sys.exit(1)
    
    # Ejecutar pruebas
    frontend_success = test_frontend_simulation()
    api_success = test_direct_api_call()
    
    print("\n=== RESUMEN ===\n")
    
    if frontend_success:
        print("✓ La simulación frontend funciona correctamente")
        print("\n🔍 POSIBLES CAUSAS DEL PROBLEMA:")
        print("   1. Problema específico del navegador (caché, cookies)")
        print("   2. Conflicto con otros scripts JavaScript")
        print("   3. Problema de timing en el frontend")
        print("   4. Error en el manejo de respuestas asíncronas")
        print("\n💡 RECOMENDACIONES:")
        print("   - Limpiar caché del navegador")
        print("   - Revisar la consola del navegador para errores JS")
        print("   - Verificar que no hay conflictos entre scripts")
    else:
        print("❌ La simulación frontend también falla")
        print("\n🔍 El problema está en el backend o configuración del servidor")
        print("\n💡 RECOMENDACIONES:")
        print("   - Revisar logs del servidor Flask")
        print("   - Verificar configuración de CSRF")
        print("   - Comprobar middleware y filtros de seguridad")
    
    if api_success:
        print("\n✓ La protección CSRF funciona correctamente")
    else:
        print("\n❌ Problema con la protección CSRF")