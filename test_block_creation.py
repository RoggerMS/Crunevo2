#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar la creación de bloques en personal-space
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json

def test_block_creation():
    """Prueba la creación de bloques via API"""
    print("=== TEST BLOCK CREATION ===")
    
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    try:
        # 1. Login
        print("\n1. 🔐 Realizando login...")
        login_response = session.get(urljoin(base_url, "/login"))
        soup = BeautifulSoup(login_response.text, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrf_token'})
        
        if not csrf_input:
            print("❌ No se encontró CSRF token en login")
            return False
            
        csrf_token = csrf_input.get('value')
        
        login_data = {
            'username': 'testuser',
            'password': 'testpass123',
            'csrf_token': csrf_token
        }
        
        login_post = session.post(urljoin(base_url, "/login"), data=login_data)
        
        if login_post.status_code != 302:
            print(f"❌ Error en login: {login_post.status_code}")
            print(f"Response: {login_post.text[:500]}")
            return False
            
        print("✅ Login exitoso")
        
        # 2. Acceder directamente a personal-space (evitar /feed/ que tiene error 500)
        print("\n2. 📄 Obteniendo página de personal space...")
        ps_response = session.get(urljoin(base_url, "/personal-space"))
        if ps_response.status_code != 200:
            print(f"❌ Error obteniendo personal space: {ps_response.status_code}")
            print(f"Response: {ps_response.text[:500]}")
            return False
            
        # Extraer meta CSRF token
        soup = BeautifulSoup(ps_response.text, 'html.parser')
        meta_csrf = soup.find('meta', {'name': 'csrf-token'})
        if not meta_csrf:
            print(f"❌ No se encontró meta CSRF token")
            print(f"HTML head: {soup.head}")
            return False
            
        meta_csrf_token = meta_csrf.get('content')
        print(f"✅ Meta CSRF token obtenido: {meta_csrf_token[:20]}...")
        
        # 3. Probar creación de un bloque simple
        print(f"\n3. 🧱 Creando bloque tipo 'nota'...")
        
        headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': meta_csrf_token,
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        block_data = {
            'type': 'nota',
            'title': 'Test nota',
            'content': 'Contenido de prueba',
            'metadata': {
                'color': 'indigo',
                'icon': 'bi-card-text'
            }
        }
        
        response = session.post(
            urljoin(base_url, '/api/personal-space/blocks'),
            json=block_data,
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('success'):
                    print(f"✅ Bloque 'nota' creado exitosamente")
                    print(f"   ID: {data.get('block', {}).get('id')}")
                    print(f"   Título: {data.get('block', {}).get('title')}")
                    return True
                else:
                    print(f"❌ Error en respuesta: {data.get('message', 'Sin mensaje')}")
                    print(f"   Respuesta completa: {data}")
                    return False
            except json.JSONDecodeError:
                print(f"❌ Error decodificando JSON")
                print(f"   Respuesta: {response.text[:500]}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"   Respuesta: {response.text[:500]}")
            
            # Si es 500, intentar obtener más detalles
            if response.status_code == 500:
                print("\n🔍 Detalles del error 500:")
                try:
                    error_data = response.json()
                    print(f"   Error JSON: {error_data}")
                except:
                    print(f"   Error HTML: {response.text[:1000]}")
            return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_block_creation()
    if success:
        print("\n🎉 ¡Prueba exitosa! La creación de bloques funciona correctamente.")
    else:
        print("\n💥 Prueba fallida. Hay problemas con la creación de bloques.")