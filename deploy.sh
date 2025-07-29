#!/bin/bash

# Script de despliegue para CRUNEVO en Fly.io (Brasil - gru)

echo "🚀 Iniciando despliegue de CRUNEVO en Brasil (gru)..."

# Verificar que flyctl esté instalado
if ! command -v flyctl &> /dev/null; then
    echo "❌ Error: flyctl no está instalado. Por favor instálalo desde https://fly.io/docs/hands-on/install-flyctl/"
    exit 1
fi

# Verificar que estemos en el directorio correcto
if [ ! -f "fly.toml" ]; then
    echo "❌ Error: No se encontró fly.toml. Asegúrate de estar en el directorio raíz del proyecto."
    exit 1
fi

# Verificar que las variables de entorno estén configuradas
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  Advertencia: DATABASE_URL no está configurada"
fi

if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  Advertencia: SECRET_KEY no está configurada"
fi

# Construir y desplegar aplicación principal
echo "📦 Construyendo aplicación principal..."
flyctl deploy --remote-only

# Verificar el estado del despliegue
echo "🔍 Verificando estado del despliegue..."
flyctl status

# Mostrar logs si hay errores
echo "📋 Mostrando logs recientes..."
flyctl logs

echo "✅ Despliegue completado!"
echo "🌐 URL Principal: https://crunevo2.fly.dev"
echo "🔧 Admin Panel: https://burrito.crunevo.com"
echo "📍 Región: Brasil (gru)" 