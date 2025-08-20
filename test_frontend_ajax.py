#!/usr/bin/env python3
"""
Test Frontend AJAX Communication
Simula exactamente las peticiones AJAX del frontend
"""

import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin


def test_frontend_ajax():
    """Simula exactamente las peticiones AJAX del frontend"""
    print("=== TEST FRONTEND AJAX COMMUNICATION ===")
    print()

    base_url = "http://localhost:5000"
    session = requests.Session()

    try:
        # 1. Primero hacer login para obtener sesión autenticada
        print("1. 🔐 Haciendo login...")
        login_response = session.get(urljoin(base_url, "/login"))
        if login_response.status_code != 200:
            print(f"❌ Error obteniendo página de login: {login_response.status_code}")
            return False

        # Extraer CSRF token del formulario de login
        soup = BeautifulSoup(login_response.text, "html.parser")
        csrf_input = soup.find("input", {"name": "csrf_token"})
        if not csrf_input:
            print("❌ No se encontró CSRF token en login")
            return False

        csrf_token = csrf_input.get("value")
        print(f"✅ CSRF token obtenido: {csrf_token[:20]}...")

        # Hacer login con usuario de prueba
        login_data = {
            "username": "testuser",
            "password": "testpass123",
            "csrf_token": csrf_token,
        }

        login_post = session.post(
            urljoin(base_url, "/login"), data=login_data, allow_redirects=False
        )

        if login_post.status_code not in [200, 302]:
            print(f"❌ Error en login: {login_post.status_code}")
            print(f"Response: {login_post.text[:500]}")
            return False

        print("✅ Login exitoso")

        # 2. Obtener página de personal space para conseguir meta CSRF token
        print("\n2. 📄 Obteniendo página de personal space...")
        ps_response = session.get(urljoin(base_url, "/personal-space"))
        if ps_response.status_code != 200:
            print(f"❌ Error obteniendo personal space: {ps_response.status_code}")
            return False

        # Extraer meta CSRF token
        soup = BeautifulSoup(ps_response.text, "html.parser")
        meta_csrf = soup.find("meta", {"name": "csrf-token"})
        if not meta_csrf:
            print("❌ No se encontró meta CSRF token")
            return False

        meta_csrf_token = meta_csrf.get("content")
        print(f"✅ Meta CSRF token obtenido: {meta_csrf_token[:20]}...")

        # 3. Simular petición AJAX exactamente como el frontend
        print("\n3. 🚀 Simulando petición AJAX...")

        # Datos del bloque como los envía el frontend
        block_data = {
            "type": "nota",
            "title": "Test Note from AJAX",
            "description": "Contenido de prueba desde AJAX",
            "category": "personal",
            "priority": "medium",
        }

        # Headers exactos como los envía csrfFetch
        headers = {
            "Content-Type": "application/json",
            "X-CSRFToken": meta_csrf_token,
            "X-Requested-With": "XMLHttpRequest",
            "X-Device-Token": "test-device-token-12345",
            "Accept": "application/json",
            "Referer": urljoin(base_url, "/personal-space"),
        }

        print(f"📤 Enviando datos: {json.dumps(block_data, indent=2)}")
        print(f"📋 Headers: {json.dumps(dict(headers), indent=2)}")

        # Hacer la petición AJAX
        ajax_response = session.post(
            urljoin(base_url, "/api/personal-space/blocks"),
            json=block_data,
            headers=headers,
        )

        print("\n📥 Respuesta del servidor:")
        print(f"Status Code: {ajax_response.status_code}")
        print(f"Headers: {dict(ajax_response.headers)}")

        if ajax_response.status_code == 302:
            print(f"🔄 Redirección a: {ajax_response.headers.get('Location')}")
            print("❌ El servidor está redirigiendo - problema de autenticación")
            return False
        elif ajax_response.status_code == 200:
            try:
                response_data = ajax_response.json()
                print(f"✅ Respuesta JSON: {json.dumps(response_data, indent=2)}")
                return True
            except json.JSONDecodeError:
                print("❌ Respuesta no es JSON válido:")
                print(ajax_response.text[:500])
                return False
        else:
            print(f"❌ Error en petición AJAX: {ajax_response.status_code}")
            print(f"Respuesta: {ajax_response.text[:500]}")
            return False

    except Exception as e:
        print(f"❌ Error durante la prueba: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_csrf_token_validation():
    """Prueba específica de validación de CSRF token"""
    print("\n=== TEST CSRF TOKEN VALIDATION ===")

    base_url = "http://localhost:5000"
    session = requests.Session()

    try:
        # Login primero
        login_response = session.get(urljoin(base_url, "/login"))
        soup = BeautifulSoup(login_response.text, "html.parser")
        csrf_input = soup.find("input", {"name": "csrf_token"})
        csrf_token = csrf_input.get("value")

        login_data = {
            "username": "testuser",
            "password": "testpass123",
            "csrf_token": csrf_token,
        }

        session.post(urljoin(base_url, "/login"), data=login_data)

        # Obtener página de personal space
        ps_response = session.get(urljoin(base_url, "/personal-space"))
        soup = BeautifulSoup(ps_response.text, "html.parser")
        meta_csrf = soup.find("meta", {"name": "csrf-token"})
        meta_csrf_token = meta_csrf.get("content")

        # Test 1: Con CSRF token correcto
        print("\n🧪 Test 1: Con CSRF token correcto")
        headers_correct = {
            "Content-Type": "application/json",
            "X-CSRFToken": meta_csrf_token,
            "X-Requested-With": "XMLHttpRequest",
        }

        response = session.post(
            urljoin(base_url, "/api/personal-space/blocks"),
            json={"type": "nota", "title": "Test"},
            headers=headers_correct,
        )
        print(f"Status: {response.status_code}")

        # Test 2: Sin CSRF token
        print("\n🧪 Test 2: Sin CSRF token")
        headers_no_csrf = {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
        }

        response = session.post(
            urljoin(base_url, "/api/personal-space/blocks"),
            json={"type": "nota", "title": "Test"},
            headers=headers_no_csrf,
        )
        print(f"Status: {response.status_code}")

        # Test 3: Con CSRF token incorrecto
        print("\n🧪 Test 3: Con CSRF token incorrecto")
        headers_wrong_csrf = {
            "Content-Type": "application/json",
            "X-CSRFToken": "token-incorrecto-12345",
            "X-Requested-With": "XMLHttpRequest",
        }

        response = session.post(
            urljoin(base_url, "/api/personal-space/blocks"),
            json={"type": "nota", "title": "Test"},
            headers=headers_wrong_csrf,
        )
        print(f"Status: {response.status_code}")

    except Exception as e:
        print(f"❌ Error en test CSRF: {str(e)}")


if __name__ == "__main__":
    print("🧪 TESTING FRONTEND AJAX COMMUNICATION")
    print("=" * 50)

    success = test_frontend_ajax()
    test_csrf_token_validation()

    print("\n" + "=" * 50)
    if success:
        print("✅ FRONTEND AJAX FUNCIONA CORRECTAMENTE")
        print("\n🔍 EL PROBLEMA PUEDE ESTAR EN:")
        print("   - JavaScript del navegador")
        print("   - Configuración de cookies")
        print("   - Manejo de errores en el frontend")
    else:
        print("❌ PROBLEMA EN COMUNICACIÓN AJAX")
        print("\n🔧 REVISAR:")
        print("   - Autenticación de usuario")
        print("   - Validación de CSRF token")
        print("   - Configuración del servidor")
