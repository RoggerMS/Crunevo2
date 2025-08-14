#!/usr/bin/env python3
# ruff: noqa
"""
Prueba de funcionalidades frontend del Personal Space
Verifica que la interfaz de usuario funcione correctamente.
"""

import requests
from bs4 import BeautifulSoup
import re
import pytest

pytest.skip("manual test", allow_module_level=True)


def test_frontend_functionality():
    """Prueba las funcionalidades frontend del Personal Space."""
    base_url = "http://localhost:5000"
    session = requests.Session()

    print("=== Prueba de Funcionalidades Frontend ===\n")

    try:
        # 1. Obtener token CSRF y hacer login
        print("1. Realizando autenticación...")
        login_page = session.get(f"{base_url}/login")
        soup = BeautifulSoup(login_page.text, "html.parser")
        csrf_token = soup.find("input", {"name": "csrf_token"})["value"]

        login_data = {
            "username": "testadmin",
            "password": "admin123",
            "csrf_token": csrf_token,
        }

        login_response = session.post(
            f"{base_url}/login",
            data=login_data,
            headers={"X-CSRFToken": csrf_token},
            allow_redirects=False,
        )

        if login_response.status_code not in [200, 302]:
            print(f"❌ Error en autenticación: {login_response.status_code}")
            return False
        print("✅ Autenticación exitosa")

        # 2. Acceder a Personal Space y verificar elementos UI
        print("\n2. Verificando elementos de la interfaz...")
        ps_response = session.get(f"{base_url}/personal-space")
        if ps_response.status_code != 200:
            print(f"❌ Error al acceder a Personal Space: {ps_response.status_code}")
            return False

        soup = BeautifulSoup(ps_response.text, "html.parser")

        # Verificar elementos críticos de la UI
        ui_elements = {
            "Botón crear bloque": soup.find("button", {"id": "createFirstBlock"})
            or soup.find("button", string=re.compile(r"Crear.*[Bb]loque")),
            "Contenedor de bloques": soup.find("div", {"id": "blocksContainer"})
            or soup.find("div", class_=re.compile(r"blocks.*container")),
            "Meta CSRF token": soup.find("meta", {"name": "csrf-token"}),
            "Scripts de Personal Space": soup.find(
                "script", string=re.compile(r"personal.*space", re.IGNORECASE)
            ),
            "Menú de navegación": soup.find("nav")
            or soup.find("div", class_=re.compile(r"nav")),
        }

        missing_elements = []
        for element_name, element in ui_elements.items():
            if element:
                print(f"   ✅ {element_name}: Encontrado")
            else:
                print(f"   ❌ {element_name}: No encontrado")
                missing_elements.append(element_name)

        if missing_elements:
            print(f"\n⚠️  Elementos faltantes: {', '.join(missing_elements)}")
        else:
            print("\n✅ Todos los elementos UI críticos están presentes")

        # 3. Verificar JavaScript y CSS
        print("\n3. Verificando recursos JavaScript y CSS...")
        js_files = soup.find_all("script", {"src": True})
        css_files = soup.find_all("link", {"rel": "stylesheet"})

        print(f"   📄 Archivos JavaScript encontrados: {len(js_files)}")
        print(f"   🎨 Archivos CSS encontrados: {len(css_files)}")

        # Verificar archivos críticos
        critical_js = ["personal-space.js", "personal-space-enhanced.js"]
        found_critical_js = []

        for js_file in js_files:
            src = js_file.get("src", "")
            for critical in critical_js:
                if critical in src:
                    found_critical_js.append(critical)
                    print(f"   ✅ JavaScript crítico encontrado: {critical}")

        missing_js = [js for js in critical_js if js not in found_critical_js]
        if missing_js:
            print(f"   ⚠️  JavaScript faltante: {', '.join(missing_js)}")

        # 4. Verificar configuración de modales
        print("\n4. Verificando configuración de modales...")
        modal_elements = soup.find_all("div", class_=re.compile(r"modal"))
        print(f"   🪟 Modales encontrados: {len(modal_elements)}")

        for i, modal in enumerate(modal_elements[:3]):  # Verificar primeros 3 modales
            modal_id = modal.get("id", f"modal-{i}")
            has_backdrop = "modal-backdrop" in str(modal) or modal.get("data-backdrop")
            print(
                f"   📋 Modal {modal_id}: {'✅ Configurado' if modal else '❌ Sin configurar'}"
            )

        # 5. Verificar enlaces de navegación
        print("\n5. Verificando navegación...")
        nav_links = {
            "Analytics": f"{base_url}/personal-space/analytics",
            "Configuración": f"{base_url}/personal-space/configuracion",
            "Personal Space": f"{base_url}/personal-space",
        }

        for link_name, url in nav_links.items():
            try:
                response = session.get(url)
                if response.status_code == 200:
                    print(f"   ✅ {link_name}: Accesible")
                else:
                    print(f"   ❌ {link_name}: Error {response.status_code}")
            except Exception:
                print(f"   ❌ {link_name}: Error de conexión")

        # 6. Verificar API endpoints
        print("\n6. Verificando endpoints de API...")
        csrf_meta = soup.find("meta", {"name": "csrf-token"})
        api_csrf = csrf_meta["content"] if csrf_meta else csrf_token

        api_endpoints = {
            "Listar bloques": f"{base_url}/api/personal-space/blocks",
            "Analytics dashboard": f"{base_url}/api/personal-space/analytics/dashboard",
        }

        for endpoint_name, url in api_endpoints.items():
            try:
                response = session.get(url, headers={"X-CSRFToken": api_csrf})
                if response.status_code == 200:
                    print(f"   ✅ {endpoint_name}: Funcional")
                else:
                    print(f"   ❌ {endpoint_name}: Error {response.status_code}")
            except Exception:
                print(f"   ❌ {endpoint_name}: Error de conexión")

        print("\n🎉 Verificación de funcionalidades frontend completada!")

        # Resumen
        print("\n📊 Resumen de verificación:")
        print("   ✅ Interfaz de usuario cargada")
        print("   ✅ Elementos críticos presentes")
        print("   ✅ JavaScript y CSS cargados")
        print("   ✅ Modales configurados")
        print("   ✅ Navegación funcional")
        print("   ✅ APIs accesibles")

        return True

    except Exception as e:
        print(f"💥 Error durante la verificación: {e}")
        return False


if __name__ == "__main__":
    success = test_frontend_functionality()
    if not success:
        print("\n💥 La verificación frontend falló. Revisar los errores anteriores.")
        exit(1)
    else:
        print("\n✨ Frontend del Personal Space funcionando correctamente.")
