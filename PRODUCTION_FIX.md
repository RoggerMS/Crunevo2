# Corrección de Problemas de Producción en Fly.io

## Problema Identificado

El problema principal era la configuración de cookies de sesión. La aplicación estaba configurada con `SESSION_COOKIE_SECURE = not DEBUG`, pero en producción con Fly.io se necesita `SESSION_COOKIE_SECURE = True` porque usa HTTPS.

## Cambios Realizados

### 1. Configuración Mejorada en `crunevo/config.py`

```python
# Antes
DEBUG = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
SESSION_COOKIE_SECURE = not DEBUG

# Después
DEBUG = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
FLASK_ENV = os.getenv("FLASK_ENV", "development")
IS_PRODUCTION = FLASK_ENV == "production"
SESSION_COOKIE_SECURE = IS_PRODUCTION
```

### 2. Scripts de Diagnóstico Creados

- `production_debug.py`: Script para diagnosticar problemas en producción
- `fix_production.sh`: Script para automatizar la corrección de problemas

## Instrucciones para Deployar

### Opción 1: Deploy Automático

```bash
# Ejecutar el script de deploy existente
./deploy.sh
```

### Opción 2: Deploy Manual

```bash
# 1. Verificar que flyctl esté instalado
flyctl version

# 2. Deployar los cambios
flyctl deploy -a crunevo2

# 3. Verificar el estado
flyctl status -a crunevo2

# 4. Ver logs para verificar que no hay errores
flyctl logs -a crunevo2
```

### Opción 3: Diagnóstico Completo

```bash
# Ejecutar el script de diagnóstico
./fix_production.sh
```

## Verificación Post-Deploy

### 1. Verificar Variables de Entorno

```bash
flyctl config show -a crunevo2
```

Debe mostrar:
- `FLASK_ENV = 'production'`
- `PORT = "8080"`
- `SESSION_COOKIE_HTTPONLY = "true"`

### 2. Verificar Secretos

```bash
flyctl secrets list -a crunevo2
```

Debe incluir:
- `DATABASE_URL`
- `SECRET_KEY`

### 3. Ejecutar Diagnóstico en Producción

```bash
# Conectarse a la instancia
flyctl ssh console -a crunevo2

# Dentro de la instancia, ejecutar:
cd /app
python production_debug.py
```

### 4. Verificar Login

Acceder a la aplicación y probar el login con:
- Usuario: `estudiante@crunevo.com`
- Contraseña: `test`

## Problemas Comunes y Soluciones

### Error de Cookies de Sesión

**Síntoma**: Redirección infinita entre `/login` y `/feed/`

**Solución**: Verificar que `SESSION_COOKIE_SECURE = True` en producción

### Error de Base de Datos

**Síntoma**: Errores de conexión a PostgreSQL

**Solución**: 
```bash
# Verificar conexión a la base de datos
flyctl postgres connect -a crunevo-db

# Ejecutar migraciones
flyctl ssh console -a crunevo2 -C "cd /app && flask db upgrade"
```

### Error de Usuario No Encontrado

**Síntoma**: Usuario 'estudiante' no existe

**Solución**:
```bash
# Crear usuario de prueba en producción
flyctl ssh console -a crunevo2 -C "cd /app && python create_student_user.py"
```

## Monitoreo Continuo

### Ver Logs en Tiempo Real

```bash
flyctl logs -a crunevo2 -f
```

### Verificar Estado de la Aplicación

```bash
flyctl status -a crunevo2
```

### Verificar Métricas

```bash
flyctl metrics -a crunevo2
```

## Contacto de Soporte

Si los problemas persisten después de seguir estos pasos:

1. Revisar los logs detallados: `flyctl logs -a crunevo2 --limit 100`
2. Ejecutar el diagnóstico completo: `python production_debug.py`
3. Verificar la configuración de la base de datos
4. Contactar al equipo de desarrollo con los logs específicos