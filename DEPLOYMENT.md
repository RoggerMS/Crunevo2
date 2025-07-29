# 🚀 Guía de Despliegue - CRUNEVO

## 📍 Región de Despliegue
- **Región Principal**: `gru` (São Paulo, Brasil)
- **Razón**: Mejor rendimiento y estabilidad para usuarios latinoamericanos

## 🛠️ Configuración de Fly.io

### Aplicación Principal (crunevo2)
```bash
# Desplegar aplicación principal
./deploy.sh
```

### Panel de Administración (crunevo-admin)
```bash
# Desplegar panel de administración
./deploy-admin.sh
```

## 🔧 Variables de Entorno Requeridas

### Para Aplicación Principal
```bash
DATABASE_URL=postgresql://user:pass@host:port/db
SECRET_KEY=your-secret-key
FLASK_ENV=production
```

### Para Panel de Administración
```bash
DATABASE_URL=postgresql://user:pass@host:port/db
SECRET_KEY=your-secret-key
FLASK_ENV=production
ADMIN_INSTANCE=1
MAINTENANCE_MODE=0
```

## 📊 URLs de Despliegue

### Aplicación Principal
- **URL**: https://crunevo2.fly.dev
- **Región**: Brasil (gru)
- **Config**: `fly.toml`

### Panel de Administración
- **URL**: https://burrito.crunevo.com
- **Región**: Brasil (gru)
- **Config**: `fly-admin.toml`

## 🔍 Monitoreo y Logs

### Ver Logs de Aplicación Principal
```bash
flyctl logs --app crunevo2
```

### Ver Logs de Panel de Administración
```bash
flyctl logs --app crunevo-admin
```

### Ver Estado de las Aplicaciones
```bash
flyctl status --app crunevo2
flyctl status --app crunevo-admin
```

## 🚨 Solución de Problemas

### Error de Migración
Si hay errores en `flask db upgrade`:
```bash
# Verificar migraciones
flyctl ssh console --app crunevo2
flask db current
flask db history
```

### Error de Dependencias
Si hay errores de importación:
```bash
# Reconstruir imagen
flyctl deploy --remote-only --no-cache
```

### Error de Memoria
Si la aplicación se queda sin memoria:
```bash
# Aumentar memoria en fly.toml
memory_mb = 2048
```

## 📈 Métricas y Monitoreo

### Panel de Administración Mejorado
- **Dashboard Avanzado**: Métricas en tiempo real
- **Sistema de Alertas**: CPU, memoria, disco
- **Analytics**: Usuarios, contenido, comercio
- **Exportación**: Datos a Excel
- **Monitoreo**: Estado del sistema

### Nuevas Funcionalidades
- ✅ Métricas del sistema en tiempo real
- ✅ Dashboard interactivo con Chart.js
- ✅ Exportación de datos a Excel
- ✅ Sistema de alertas automáticas
- ✅ Monitoreo de rendimiento
- ✅ Gestión avanzada de usuarios y clubes

## 🔄 Actualizaciones

### Desplegar Cambios
```bash
# Aplicación principal
flyctl deploy --app crunevo2

# Panel de administración
flyctl deploy --app crunevo-admin --config fly-admin.toml
```

### Rollback en Caso de Problemas
```bash
flyctl deploy --app crunevo2 --image-label v1
```

## 📞 Soporte

Para problemas de despliegue:
1. Verificar logs: `flyctl logs`
2. Verificar estado: `flyctl status`
3. Revisar configuración: `fly.toml` y `fly-admin.toml`
4. Contactar al equipo de desarrollo

---

**Última actualización**: Julio 2025
**Versión**: 2.0 con mejoras de admin 