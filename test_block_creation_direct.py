#!/usr/bin/env python3
"""
Script para probar la creación de bloques directamente con el backend
sin depender de autenticación web
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crunevo.app import create_app
from crunevo.extensions import db
from crunevo.models import User, PersonalSpaceBlock
from crunevo.services.block_service import BlockService
from crunevo.services.validation_service import ValidationService


def test_block_creation_direct():
    """Prueba la creación de bloques directamente con el backend"""
    print("🧪 PRUEBA DIRECTA DE CREACIÓN DE BLOQUES")
    print("=" * 50)

    # Crear la aplicación Flask
    app = create_app()

    with app.app_context():
        try:
            # 1. Verificar o crear usuario de prueba
            print("👤 Verificando usuario de prueba...")
            test_user = User.query.filter_by(email="test@crunevo.com").first()

            if not test_user:
                print("📝 Creando usuario de prueba...")
                test_user = User(
                    username="testuser",
                    email="test@crunevo.com",
                    password_hash="test_hash",  # En producción usar hash real
                    activated=True,
                )
                db.session.add(test_user)
                db.session.commit()
                print(f"✅ Usuario creado: {test_user.username} (ID: {test_user.id})")
            else:
                print(
                    f"✅ Usuario encontrado: {test_user.username} (ID: {test_user.id})"
                )

            # 2. Probar ValidationService
            print("\n🔍 Probando ValidationService...")
            test_data = {
                "type": "nota",
                "title": "Nota de prueba",
                "content": "Contenido de prueba",
                "metadata": {"color": "blue", "priority": "medium"},
            }

            validation_result = ValidationService.validate_block_data(test_data)
            print(f"Validación: {validation_result}")

            if not validation_result["valid"]:
                print(f"❌ Error de validación: {validation_result['errors']}")
                return False

            print("✅ Datos válidos")

            # 3. Probar BlockService
            print("\n🔧 Probando BlockService...")

            # Crear bloque
            block = BlockService.create_block(test_user.id, test_data)
            print(f"✅ Bloque creado: {block.id} - {block.title}")

            # Verificar que se guardó en la base de datos
            saved_block = PersonalSpaceBlock.query.filter_by(id=block.id).first()
            if saved_block:
                print(f"✅ Bloque verificado en BD: {saved_block.title}")
            else:
                print("❌ Bloque no encontrado en BD")
                return False

            # 4. Probar actualización
            print("\n📝 Probando actualización...")
            update_data = {
                "title": "Nota actualizada",
                "content": "Contenido actualizado",
            }

            updated_block = BlockService.update_block(
                block.id, test_user.id, update_data
            )
            if updated_block:
                print(f"✅ Bloque actualizado: {updated_block.title}")
            else:
                print("❌ Error al actualizar bloque")
                return False

            # 5. Probar eliminación
            print("\n🗑️ Probando eliminación...")
            success = BlockService.delete_block(block.id, test_user.id)
            if success:
                print("✅ Bloque eliminado exitosamente")
            else:
                print("❌ Error al eliminar bloque")
                return False

            # 6. Verificar eliminación
            deleted_block = PersonalSpaceBlock.query.filter_by(
                id=block.id, status="active"
            ).first()
            if not deleted_block:
                print("✅ Eliminación verificada")
            else:
                print("❌ El bloque aún existe como activo")
                return False

            print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
            print("\n✅ El backend funciona correctamente")
            print("\n🔍 El problema debe estar en:")
            print("   1. Autenticación web (usuario no logueado)")
            print("   2. CSRF token (no se envía correctamente)")
            print("   3. Frontend JavaScript (errores en el código)")
            print("   4. Configuración de sesiones Flask")

            return True

        except Exception as e:
            print(f"❌ Error durante las pruebas: {e}")
            import traceback

            traceback.print_exc()
            return False


def test_api_endpoint_simulation():
    """Simula exactamente lo que hace el endpoint de la API"""
    print("\n🌐 SIMULACIÓN DEL ENDPOINT API")
    print("=" * 40)

    app = create_app()

    with app.app_context():
        try:
            # Simular request data
            request_data = {
                "type": "nota",
                "title": "Nueva nota",
                "description": "Contenido de prueba",
                "category": "personal",
                "priority": "medium",
            }

            print(f"📥 Datos de entrada: {request_data}")

            # Obtener usuario de prueba
            test_user = User.query.filter_by(email="test@crunevo.com").first()
            if not test_user:
                print("❌ Usuario de prueba no encontrado")
                return False

            print(f"👤 Usuario: {test_user.username}")

            # Procesar datos como lo hace el endpoint
            processed_data = {
                "type": request_data.get("type"),
                "title": request_data.get(
                    "title", f"Nuevo {request_data.get('type', 'bloque')}"
                ),
                "content": request_data.get("description", ""),
                "metadata": {
                    "category": request_data.get("category", "personal"),
                    "priority": request_data.get("priority", "medium"),
                    "size": request_data.get("size", "medium"),
                    "position_x": request_data.get("position_x", 0),
                    "position_y": request_data.get("position_y", 0),
                    "theme_color": request_data.get("theme_color", "blue"),
                    "header_style": request_data.get("header_style", "default"),
                    "show_border": request_data.get("show_border", False),
                    "show_shadow": request_data.get("show_shadow", False),
                    "auto_save": request_data.get("auto_save", False),
                    "notifications": request_data.get("notifications", False),
                    "collaborative": request_data.get("collaborative", False),
                    "public_view": request_data.get("public_view", False),
                    "type_specific_config": request_data.get(
                        "type_specific_config", {}
                    ),
                },
            }

            print(f"🔄 Datos procesados: {processed_data}")

            # Crear bloque
            block = BlockService.create_block(test_user.id, processed_data)

            # Simular respuesta JSON
            response = {"success": True, "block": block.to_dict()}

            print(f"📤 Respuesta simulada: {response}")
            print("\n✅ Simulación del endpoint exitosa")

            # Limpiar
            BlockService.delete_block(block.id, test_user.id)

            return True

        except Exception as e:
            print(f"❌ Error en simulación: {e}")
            import traceback

            traceback.print_exc()
            return False


if __name__ == "__main__":
    print("DIAGNÓSTICO COMPLETO DEL SISTEMA DE BLOQUES\n")

    # Ejecutar pruebas
    backend_ok = test_block_creation_direct()
    api_ok = test_api_endpoint_simulation()

    print("\n" + "=" * 60)
    print("RESUMEN FINAL")
    print("=" * 60)

    if backend_ok and api_ok:
        print("\n✅ EL BACKEND FUNCIONA PERFECTAMENTE")
        print("\n🔍 EL PROBLEMA ESTÁ EN EL FRONTEND:")
        print("\n   1. 🔐 AUTENTICACIÓN:")
        print("      - El usuario no está logueado")
        print("      - Las cookies de sesión no se envían")
        print("      - Problema con @login_required")
        print("\n   2. 🛡️ CSRF PROTECTION:")
        print("      - Token CSRF no se obtiene correctamente")
        print("      - Header X-CSRFToken no se envía")
        print("      - Token CSRF inválido o expirado")
        print("\n   3. 📡 COMUNICACIÓN AJAX:")
        print("      - Error en la función csrfFetch")
        print("      - Problema en personal-space.js")
        print("      - Headers incorrectos en la petición")
        print("\n   4. 🌐 CONFIGURACIÓN DEL SERVIDOR:")
        print("      - Problema con Flask-Login")
        print("      - Configuración de sesiones")
        print("      - Middleware de seguridad")
        print("\n💡 PRÓXIMOS PASOS:")
        print("   1. Verificar que el usuario esté logueado en el navegador")
        print("   2. Revisar la consola del navegador para errores")
        print("   3. Comprobar que se envía el token CSRF")
        print("   4. Verificar las cookies de sesión")
    else:
        print("\n❌ HAY PROBLEMAS EN EL BACKEND")
        print("\n🔧 REVISAR:")
        print("   - Configuración de la base de datos")
        print("   - Servicios BlockService y ValidationService")
        print("   - Modelos de datos")
        print("   - Logs del servidor")
