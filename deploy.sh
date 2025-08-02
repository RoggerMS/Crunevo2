#!/bin/bash

# Script unificado para despliegue de CRUNEVO en Fly.io
# Uso:
# ./deploy.sh app      - Despliega la aplicación principal
# ./deploy.sh admin    - Despliega el panel de administración
# ./deploy.sh all      - Despliega ambos
# ./deploy.sh          - Muestra este mensaje de ayuda

# --- Configuración ---
set -eo pipefail # Salir inmediatamente si un comando falla

APP_NAME="crunevo2"
ADMIN_APP_NAME="crunevo-admin"

APP_CONFIG="fly.toml"
ADMIN_CONFIG="fly-admin.toml"

# --- Funciones ---

# Muestra el mensaje de ayuda
show_help() {
    echo "Uso: $0 {app|admin|all}"
    echo "  app:   Despliega la aplicación principal (${APP_NAME})"
    echo "  admin: Despliega el panel de administración (${ADMIN_APP_NAME})"
    echo "  all:   Despliega ambos, primero la app y luego el admin."
}

# Verifica dependencias y variables de entorno
check_prerequisites() {
    echo "🔎 Verificando prerrequisitos..."
    if ! command -v flyctl &> /dev/null; then
        echo "❌ Error: flyctl no está instalado. Por favor instálalo desde https://fly.io/docs/hands-on/install-flyctl/"
        exit 1
    fi

    if [ -z "$DATABASE_URL" ]; then
        echo "⚠️  Advertencia: La variable de entorno DATABASE_URL no está configurada."
    fi

    if [ -z "$SECRET_KEY" ]; then
        echo "⚠️  Advertencia: La variable de entorno SECRET_KEY no está configurada."
    fi
    echo "✅ Prerrequisitos verificados."
}

# Función para desplegar un target específico
deploy_target() {
    local target_name="$1"
    local config_file="$2"
    local app_fly_name="$3"

    echo ""
    echo "🚀 Iniciando despliegue de '${target_name}'..."

    if [ ! -f "${config_file}" ]; then
        echo "❌ Error: No se encontró ${config_file}. Asegúrate de estar en el directorio raíz del proyecto."
        exit 1
    fi

    echo "📦 Construyendo y desplegando..."
    if flyctl deploy --config "${config_file}" --remote-only; then
        echo "✅ Despliegue de '${target_name}' completado exitosamente."
        echo "🔍 Verificando estado..."
        flyctl status --app "${app_fly_name}"
    else
        echo "❌ Error durante el despliegue de '${target_name}'."
        echo "📋 Mostrando logs para diagnóstico..."
        flyctl logs --app "${app_fly_name}"
        exit 1 # Salir si el despliegue falla
    fi
}

# --- Lógica Principal ---

# Verificar dependencias al inicio
check_prerequisites

case "$1" in
    app)
        deploy_target "Aplicación Principal" "${APP_CONFIG}" "${APP_NAME}"
        ;;
    admin)
        deploy_target "Panel de Administración" "${ADMIN_CONFIG}" "${ADMIN_APP_NAME}"
        ;;
    all)
        echo "🌍 Iniciando despliegue completo..."
        deploy_target "Aplicación Principal" "${APP_CONFIG}" "${APP_NAME}"
        deploy_target "Panel de Administración" "${ADMIN_CONFIG}" "${ADMIN_APP_NAME}"
        echo "✨ ¡Despliegue completo de ambas aplicaciones finalizado!"
        ;;
    *)
        show_help
        exit 1
        ;;
esac

echo ""
echo "🎉 Proceso finalizado."