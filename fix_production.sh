#!/bin/bash

# Script para diagnosticar y corregir problemas en producción

set -e

echo "🔧 DIAGNÓSTICO Y CORRECCIÓN DE PRODUCCIÓN"
echo "=========================================="

# Verificar que flyctl esté instalado
if ! command -v flyctl &> /dev/null; then
    echo "❌ Error: flyctl no está instalado"
    exit 1
fi

# Función para ejecutar comandos en la app de producción
run_in_production() {
    echo "📡 Ejecutando en producción: $1"
    flyctl ssh console -a crunevo2 -C "$1"
}

# Función para verificar el estado de la aplicación
check_app_status() {
    echo "🔍 Verificando estado de la aplicación..."
    flyctl status -a crunevo2
    echo ""
}

# Función para verificar logs recientes
check_logs() {
    echo "📋 Logs recientes de la aplicación:"
    flyctl logs -a crunevo2 --limit 20
    echo ""
}

# Función para ejecutar diagnóstico en producción
run_production_debug() {
    echo "🔍 Ejecutando diagnóstico en producción..."
    
    # Copiar el script de diagnóstico
    echo "📤 Subiendo script de diagnóstico..."
    flyctl ssh sftp -a crunevo2 shell
    
    # Ejecutar el diagnóstico
    run_in_production "cd /app && python production_debug.py"
}

# Función para verificar y corregir configuración
fix_configuration() {
    echo "🔧 Verificando configuración..."
    
    # Verificar variables de entorno
    echo "📋 Variables de entorno actuales:"
    flyctl config show -a crunevo2
    
    # Verificar secretos
    echo "🔐 Secretos configurados:"
    flyctl secrets list -a crunevo2
    
    echo ""
    echo "💡 Si hay problemas de configuración, puedes usar:"
    echo "   flyctl secrets set SECRET_KEY=\"tu_clave_secreta\" -a crunevo2"
    echo "   flyctl secrets set DATABASE_URL=\"tu_url_db\" -a crunevo2"
}

# Función para reiniciar la aplicación
restart_app() {
    echo "🔄 Reiniciando aplicación..."
    flyctl apps restart crunevo2
    
    echo "⏳ Esperando que la aplicación se reinicie..."
    sleep 10
    
    echo "🔍 Verificando estado después del reinicio:"
    flyctl status -a crunevo2
}

# Función para verificar la base de datos
check_database() {
    echo "🗄️  Verificando base de datos..."
    
    # Ejecutar migraciones si es necesario
    echo "📊 Ejecutando migraciones..."
    run_in_production "cd /app && flask db upgrade"
    
    # Verificar que las tablas existan
    echo "🔍 Verificando estructura de base de datos..."
    run_in_production "cd /app && python -c \"from crunevo.app import create_app; from crunevo.extensions import db; app = create_app(); app.app_context().push(); print('Tablas:', db.engine.table_names())\""
}

# Función para verificar el usuario de prueba
check_test_user() {
    echo "👤 Verificando usuario de prueba..."
    run_in_production "cd /app && python -c \"from crunevo.app import create_app; from crunevo.models.user import User; app = create_app(); app.app_context().push(); user = User.query.filter_by(username='estudiante').first(); print(f'Usuario encontrado: {user.username if user else None}')\""
}

# Función principal
main() {
    echo "🚀 Iniciando diagnóstico y corrección..."
    echo ""
    
    check_app_status
    check_logs
    fix_configuration
    
    echo ""
    echo "¿Deseas ejecutar el diagnóstico completo en producción? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        run_production_debug
        check_database
        check_test_user
    fi
    
    echo ""
    echo "¿Deseas reiniciar la aplicación? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        restart_app
    fi
    
    echo ""
    echo "✅ Proceso completado"
    echo "💡 Para más información, revisa los logs con: flyctl logs -a crunevo2"
}

# Ejecutar función principal
main "$@"