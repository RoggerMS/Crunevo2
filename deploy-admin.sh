#!/bin/bash

# Script de despliegue para Panel de Administración CRUNEVO en Fly.io (Brasil - gru)

echo "🚀 Iniciando despliegue del Panel de Administración en Brasil (gru)..."

# Verificar que flyctl esté instalado
if ! command -v flyctl &> /dev/null; then
    echo "❌ Error: flyctl no está instalado. Por favor instálalo desde https://fly.io/docs/hands-on/install-flyctl/"
    exit 1
fi

# Verificar que estemos en el directorio correcto
if [ ! -f "fly-admin.toml" ]; then
    echo "❌ Error: No se encontró fly-admin.toml. Asegúrate de estar en el directorio raíz del proyecto."
    exit 1
fi

# Verificar que las variables de entorno estén configuradas
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  Advertencia: DATABASE_URL no está configurada"
fi

if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  Advertencia: SECRET_KEY no está configurada"
fi

# Desplegar usando la configuración de admin
echo "📦 Construyendo panel de administración..."
flyctl deploy --config fly-admin.toml --remote-only

# Verificar el estado del despliegue
echo "🔍 Verificando estado del despliegue..."
flyctl status --app crunevo-admin

# Mostrar logs si hay errores
echo "📋 Mostrando logs recientes..."
flyctl logs --app crunevo-admin

echo "✅ Despliegue del Panel de Administración completado!"
echo "🔧 Admin Panel: https://burrito.crunevo.com"
echo "📍 Región: Brasil (gru)" 