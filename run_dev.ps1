# Script de desarrollo para Windows PowerShell
# Ejecuta Crunevo localmente sin problemas de SSL

Write-Host "🚀 Iniciando Crunevo en modo desarrollo..." -ForegroundColor Green

# Configurar variables de entorno para desarrollo local
$env:ENABLE_TALISMAN = "0"    # Deshabilitar Talisman (HTTPS enforcement)
$env:FORCE_HTTPS = "0"        # Deshabilitar redirección HTTPS
$env:FLASK_ENV = "development"
$env:FLASK_DEBUG = "1"

Write-Host "✅ ENABLE_TALISMAN = 0" -ForegroundColor Yellow
Write-Host "✅ FORCE_HTTPS = 0" -ForegroundColor Yellow
Write-Host "✅ FLASK_ENV = development" -ForegroundColor Yellow
Write-Host "✅ FLASK_DEBUG = 1" -ForegroundColor Yellow

Write-Host "`n📡 Iniciando servidor Flask en http://localhost:5000" -ForegroundColor Cyan
Write-Host "🔓 SSL/HTTPS deshabilitado para desarrollo local" -ForegroundColor Cyan
Write-Host "⚠️  NOTA: Estas configuraciones son solo para desarrollo local" -ForegroundColor Red
Write-Host "   En producción, Talisman y HTTPS siguen activos.`n" -ForegroundColor Red

try {
    # Ejecutar Flask
    python -m flask run --host=0.0.0.0 --port=5000 --debug
}
catch {
    Write-Host "❌ Error al ejecutar Flask: $_" -ForegroundColor Red
    exit 1
}