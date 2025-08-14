#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from bs4 import BeautifulSoup

def test_personal_space_direct():
    """Test direct access to personal-space after login"""
    
    session = requests.Session()
    base_url = "http://127.0.0.1:5000"
    
    print("=== TEST DIRECT PERSONAL SPACE ACCESS ===")
    
    try:
        # 1. Get login page and CSRF token
        print("\n1. 🔐 Obteniendo página de login...")
        login_page = session.get(f"{base_url}/login")
        if login_page.status_code != 200:
            print(f"❌ Error obteniendo login: {login_page.status_code}")
            return False
            
        soup = BeautifulSoup(login_page.content, 'html.parser')
        csrf_token = soup.find('meta', {'name': 'csrf-token'})['content']
        print(f"✅ CSRF token obtenido: {csrf_token[:20]}...")
        
        # 2. Login
        print("\n2. 🔑 Realizando login...")
        login_data = {
            'username': 'testuser',
            'password': 'testpass123',
            'csrf_token': csrf_token
        }
        
        login_response = session.post(
            f"{base_url}/login",
            data=login_data,
            headers={
                'X-CSRFToken': csrf_token,
                'X-Requested-With': 'XMLHttpRequest'
            },
            allow_redirects=False
        )
        
        if login_response.status_code == 302:
            print("✅ Login exitoso (redirect 302)")
        else:
            print(f"❌ Error en login: {login_response.status_code}")
            print(f"Response: {login_response.text[:500]}")
            return False
            
        # 3. Access personal-space directly
        print("\n3. 🏠 Accediendo a personal-space directamente...")
        ps_response = session.get(f"{base_url}/personal-space")
        
        if ps_response.status_code == 200:
            print("✅ Personal-space accesible")
            
            # Extract new CSRF token from personal-space page
            ps_soup = BeautifulSoup(ps_response.content, 'html.parser')
            new_csrf_token = ps_soup.find('meta', {'name': 'csrf-token'})['content']
            print(f"✅ Nuevo CSRF token: {new_csrf_token[:20]}...")
            
            # 4. Test block creation
            print("\n4. 📝 Probando creación de bloque...")
            block_data = {
                'type': 'nota',
                'title': 'Test Block',
                'content': 'This is a test block',
                'csrf_token': new_csrf_token
            }
            
            create_response = session.post(
                f"{base_url}/api/personal-space/blocks",
                json=block_data,
                headers={
                    'Content-Type': 'application/json',
                    'X-CSRFToken': new_csrf_token,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            )
            
            print(f"Status: {create_response.status_code}")
            
            if create_response.status_code == 200:
                try:
                    result = create_response.json()
                    print(f"✅ Bloque creado exitosamente: {result}")
                    return True
                except json.JSONDecodeError:
                    print(f"❌ Respuesta no es JSON válido: {create_response.text[:200]}")
            else:
                print(f"❌ Error creando bloque: {create_response.status_code}")
                print(f"Response: {create_response.text[:500]}")
                
        else:
            print(f"❌ Error accediendo a personal-space: {ps_response.status_code}")
            print(f"Response: {ps_response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"💥 Error durante la prueba: {str(e)}")
        return False
    
    return False

if __name__ == "__main__":
    success = test_personal_space_direct()
    if success:
        print("\n🎉 ¡Prueba exitosa! El sistema funciona correctamente.")
    else:
        print("\n💥 Prueba fallida. Hay problemas con el sistema.")