# Crunevo2

This repository contains the Crunevo2 Flask application. The project is configured to run on Fly.io using Docker and PostgreSQL.

## Deploying to Fly.io

If you encounter the error below when attempting to deploy:

```
Detected a Dockerfile app
Error: launch manifest was created for a app, but this is a app
unsuccessful command 'flyctl launch plan generate /tmp/manifest.json'
```

It usually means Fly.io detected an outdated manifest from a previous deployment attempt. To fix it and prepare a clean production environment:

1. **Remove old Fly.io configuration**
   ```bash
   rm -rf fly.toml .fly
   ```
2. **Regenerate `fly.toml` using the Dockerfile**
   ```bash
   fly launch --no-deploy --dockerfile Dockerfile --name crunevo2
   ```
   This forces Fly.io to generate a manifest that explicitly uses the Dockerfile.
3. **Ensure `fly.toml` contains:**
   ```toml
   app = "crunevo2"

   [build]
     dockerfile = "Dockerfile"

   [deploy]
     release_command = "flask db upgrade"

   [[services]]
     internal_port = 8080
     protocol = "tcp"

     [[services.ports]]
       handlers = ["http"]
       port = 8080
   ```
4. **Verify the Dockerfile** uses Gunicorn:
   ```Dockerfile
   CMD ["gunicorn", "-b", "0.0.0.0:8080", "crunevo.app:app"]
   ```
   or, alternatively, the Flask development server (not recommended for production).
5. **Deploy the application**
   ```bash
   fly deploy
   ```

`CLOUDINARY_URL` and `DATABASE_URL` are already supported in `config.py`, and `flask db upgrade` runs automatically as the release command. The feed cache uses Redis, so set `REDIS_URL` (default `redis://localhost:6379/0`) and make sure a Redis instance is available when deploying or running locally.
* Si Redis no está disponible el feed funcionará en modo "degradado"
  (lee directamente de la base de datos) y repoblará el cache
  automáticamente cuando Redis vuelva.
* El ZSET de cada usuario expira a los 7 días para evitar crecimiento infinito.
* El tamaño máximo del feed (`MAX_CACHE` en `feed_cache.py`) se puede ajustar
  según la carga; por defecto mantiene los **200** elementos más recientes.

Para correr Redis localmente de forma rápida:
```bash
docker run -d --name redis -p 6379:6379 redis:7
```

### Migrations

Para crear una nueva migración y aplicarla:

```bash
flask --app crunevo.app:create_app db migrate -m "mensaje"
flask --app crunevo.app:create_app db upgrade
```

### Variables de entorno de seguridad

```
ARGON2_TIME_COST=2
ARGON2_MEMORY_COST=102400
ARGON2_PARALLELISM=8
ENABLE_TALISMAN=true
ENABLE_CSP_OVERRIDE=false
ONBOARDING_TOKEN_EXP_H=1
```

### Verificación manual

Los administradores pueden aprobar cuentas de estudiantes desde
`/admin/verificaciones`. Al aceptar, el usuario obtiene nivel de verificación 2
y se muestra un distintivo en la barra de navegación.

### Ajustar el ranking del feed
- Fórmula en `crunevo/utils/scoring.py`
- Modificar las variables `FEED_LIKE_W`, `FEED_DL_W`, `FEED_COM_W` y
  `FEED_HALF_LIFE_H` para ajustar pesos sin tocar el código.

### Rutas


La ruta `/notes/<id>` responde tanto al endpoint `notes.detail` como a `notes.view_note` (alias para plantillas).

Ejemplo:
```
url_for('notes.detail', note_id=42)  => /notes/42
url_for('notes.view_note', id=42)   => /notes/42
```

## Contribuir y correr las pruebas

Instala las dependencias:

```bash
pip install -r requirements.txt
```

La suite usa SQLite en memoria y aplica las migraciones desde cero en cada
ejecución. Los `DeprecationWarning` de SQLAlchemy se filtran mediante
`pytest.ini` para mantener la salida limpia.

Para ejecutar formato y tests en un paso:

```bash
make test
```

Opcionalmente puedes instalar los hooks de `pre-commit` para formatear el
código automáticamente antes de cada commit:

```bash
pre-commit install
```

## Configuración

La clave CSRF (`FLASK_WTF_SECRET_KEY`) suele ser la misma que `SECRET_KEY`.
En producción la protección CSRF está siempre habilitada.

Si necesitas el token desde JavaScript puedes leerlo con:

```javascript
document.querySelector('meta[name="csrf-token"]').content;
```

