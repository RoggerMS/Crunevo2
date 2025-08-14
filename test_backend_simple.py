#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple del backend para creación de bloques
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crunevo.app import create_app
from crunevo.models.user import User
from crunevo.models.personal_space_block import PersonalSpaceBlock
from crunevo.extensions import db
from crunevo.services.block_service import BlockService
from crunevo.services.validation_service import ValidationService

def test_backend_functionality():
    """Test básico del backend"""
    print("\n🧪 TEST BACKEND PERSONAL SPACE")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. Verificar si existe un usuario
            print("\n🔍 VERIFICANDO USUARIOS EXISTENTES")
            users = User.query.limit(5).all()
            print(f"📊 Usuarios encontrados: {len(users)}")
            
            if users:
                test_user = users[0]
                print(f"✅ Usando usuario existente: {test_user.username} (ID: {test_user.id})")
            else:
                print("❌ No hay usuarios en la base de datos")
                return False
            
            # 2. Test ValidationService
            print("\n🔍 TESTING VALIDATION SERVICE")
            validation_service = ValidationService()
            
            # Datos de prueba
            block_data = {
                'type': 'nota',
                'title': 'Test Note',
                'description': 'Contenido de prueba',
                'category': 'personal',
                'priority': 'medium'
            }
            
            # Validar datos
            validation_result = validation_service.validate_block_data(block_data)
            is_valid = validation_result.get('valid', False)
            errors = validation_result.get('errors', [])
            print(f"📋 Validación: {'✅ Válido' if is_valid else '❌ Inválido'}")
            if errors:
                print(f"🚨 Errores: {errors}")
            
            # 3. Test BlockService
            print("\n🔍 TESTING BLOCK SERVICE")
            block_service = BlockService()
            
            # Crear bloque
            try:
                new_block = block_service.create_block(
                    user_id=test_user.id,
                    block_data=block_data
                )
                print(f"✅ Bloque creado exitosamente: ID {new_block.id}")
                
                # Verificar que se guardó
                saved_block = PersonalSpaceBlock.query.filter_by(id=new_block.id).first()
                if saved_block:
                    print(f"✅ Bloque verificado en BD: {saved_block.title}")
                    
                    # Limpiar - eliminar el bloque de prueba
                    db.session.delete(saved_block)
                    db.session.commit()
                    print("🧹 Bloque de prueba eliminado")
                    
                    return True
                else:
                    print("❌ Bloque no encontrado en BD")
                    return False
                    
            except Exception as e:
                print(f"❌ Error creando bloque: {str(e)}")
                return False
                
        except Exception as e:
            print(f"❌ Error general: {str(e)}")
            return False

def test_api_endpoint_simulation():
    """Simula el comportamiento del endpoint API"""
    print("\n🌐 SIMULACIÓN DEL ENDPOINT API")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Buscar usuario
            user = User.query.first()
            if not user:
                print("❌ No hay usuarios disponibles")
                return False
                
            print(f"👤 Usuario encontrado: {user.username}")
            
            # Datos de entrada (simulando request.json)
            input_data = {
                'type': 'nota',
                'title': 'Nueva nota',
                'description': 'Contenido de prueba',
                'category': 'personal',
                'priority': 'medium'
            }
            
            print(f"📥 Datos de entrada: {input_data}")
            
            # Simular el procesamiento del endpoint
            validation_service = ValidationService()
            block_service = BlockService()
            
            # Validar
            validation_result = validation_service.validate_block_data(input_data)
            is_valid = validation_result.get('valid', False)
            errors = validation_result.get('errors', [])
            if not is_valid:
                print(f"❌ Validación falló: {errors}")
                return False
                
            # Crear bloque
            block = block_service.create_block(
                user_id=user.id,
                block_data=input_data
            )
            
            # Simular respuesta JSON
            response_data = {
                'success': True,
                'message': 'Bloque creado exitosamente',
                'block': {
                    'id': block.id,
                    'title': block.title,
                    'type': block.type,
                    'created_at': block.created_at.isoformat() if block.created_at else None
                }
            }
            
            print(f"✅ Respuesta simulada: {response_data}")
            
            # Limpiar
            db.session.delete(block)
            db.session.commit()
            
            return True
            
        except Exception as e:
            print(f"❌ Error en simulación API: {str(e)}")
            return False

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("TEST BACKEND PERSONAL SPACE - DIAGNÓSTICO COMPLETO")
    print("=" * 60)
    
    # Test 1: Funcionalidad básica del backend
    backend_ok = test_backend_functionality()
    
    # Test 2: Simulación del endpoint API
    api_ok = test_api_endpoint_simulation()
    
    print("\n" + "=" * 60)
    print("RESUMEN FINAL")
    print("=" * 60)
    
    if backend_ok and api_ok:
        print("\n✅ BACKEND FUNCIONA CORRECTAMENTE")
        print("\n🔧 EL PROBLEMA ESTÁ EN EL FRONTEND:")
        print("   - Autenticación de usuario")
        print("   - Token CSRF")
        print("   - Comunicación AJAX")
        print("   - Manejo de respuestas")
    else:
        print("\n❌ HAY PROBLEMAS EN EL BACKEND")
        print("\n🔧 REVISAR:")
        print("   - Configuración de la base de datos")
        print("   - Servicios BlockService y ValidationService")
        print("   - Modelos de datos")
        print("   - Logs del servidor")