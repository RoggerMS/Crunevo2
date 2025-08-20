#!/usr/bin/env python3
"""
Script para diagnosticar problemas de login específicos
"""

import requests
from bs4 import BeautifulSoup


def test_login_debug():
    """Test login with detailed error handling"""
    base_url = "http://127.0.0.1:5000"

    # Create session
    session = requests.Session()

    print("🧪 DEBUGGING LOGIN PROCESS")
    print("=" * 50)

    try:
        # 1. Get login page
        print("1. 📄 Obteniendo página de login...")
        login_page = session.get(f"{base_url}/login")
        print(f"   Status: {login_page.status_code}")

        if login_page.status_code != 200:
            print(f"❌ Error obteniendo página de login: {login_page.status_code}")
            return

        # 2. Extract CSRF token
        soup = BeautifulSoup(login_page.text, "html.parser")
        csrf_meta = soup.find("meta", {"name": "csrf-token"})

        if not csrf_meta:
            print("❌ No se encontró CSRF token en meta tag")
            return

        csrf_token = csrf_meta.get("content")
        print(f"   ✅ CSRF token: {csrf_token[:20]}...")

        # 3. Prepare login data
        login_data = {"username": "testuser", "password": "testpass123"}

        headers = {
            "X-CSRFToken": csrf_token,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": f"{base_url}/login",
        }

        print("\n2. 🔐 Intentando login...")
        print(f"   Username: {login_data['username']}")
        print(f"   Headers: {list(headers.keys())}")

        # 4. Attempt login
        login_response = session.post(
            f"{base_url}/login", data=login_data, headers=headers, allow_redirects=False
        )

        print(f"   Status: {login_response.status_code}")
        print(f"   Headers: {dict(login_response.headers)}")

        if login_response.status_code == 500:
            print("\n❌ ERROR 500 DETECTADO")
            print("Response content:")
            print(login_response.text[:1000])

        elif login_response.status_code == 302:
            print("\n✅ REDIRECT DETECTADO (posible éxito)")
            location = login_response.headers.get("Location", "No location header")
            print(f"   Redirect to: {location}")

        elif login_response.status_code == 200:
            print("\n⚠️ STATUS 200 (posible error en form)")
            # Check for error messages in response
            soup = BeautifulSoup(login_response.text, "html.parser")
            error_divs = soup.find_all(
                "div", class_=["alert", "error", "flash-message"]
            )
            if error_divs:
                print("   Errores encontrados:")
                for error in error_divs:
                    print(f"   - {error.get_text().strip()}")
            else:
                print("   No se encontraron mensajes de error específicos")

    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión. ¿Está el servidor ejecutándose?")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_login_debug()
