# Crunevo2

This repository contains the Crunevo2 Flask application. The project is configured to run on Fly.io using Docker and PostgreSQL.

The administration panel is served from the dedicated subdomain `https://burrito.crunevo.com`.

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
4. **Verify the Dockerfile** uses Gunicorn with the eventlet worker for WebSocket support:
   ```Dockerfile
   CMD ["gunicorn", "-k", "eventlet", "-b", "0.0.0.0:8080", "crunevo.app:app"]
   ```
   or, alternatively, the Flask development server (not recommended for production).
5. **Deploy the application**
   ```bash
   fly deploy
   ```

## Troubleshooting deployment failures

If `fly deploy` fails with `release_command failed` and the logs show an
`OperationalError` when connecting to `crunevo-db.flycast`, the app could not
reach the PostgreSQL instance. Make sure a Fly Postgres cluster exists and is
attached to your application:

```bash
fly postgres create --name crunevo-db       # creates the database
fly postgres attach --postgres-app crunevo-db -a crunevo2
```

This command sets the `DATABASE_URL` secret automatically. Verify it with
`fly secrets list -a crunevo2`. If the database is stopped, restart it with
`fly pg restart -a crunevo-db` and then run `fly deploy` again.

If Fly warns that the app is not listening on `0.0.0.0:8080`, double-check that
your Dockerfile binds Gunicorn to that address and that `internal_port = 8080`
is set in `fly.toml`. You can inspect startup errors with `fly logs`.
If the warning persists even with those settings, run `fly logs -a crunevo2` to
verify Gunicorn starts correctly. Startup errors will prevent the app from
binding to port `8080` and trigger this message.

If you want to run the application locally but use a PostgreSQL
database hosted on Fly.io:
```bash
fly postgres create ...           # crea cluster
fly postgres attach ...           # genera DATABASE_URL
fly secrets set SECRET_KEY=...    # etc.
```

When connecting from another Fly app, use the internal hostname
`crunevo-db.internal` (some older docs referenced `db.internal`).

DNS notes:
* `www.crunevo.com` → CNAME `crunevo2.fly.dev`
* `crunevo.com` → A `66.241.125.104` (o AAAA si asignas IPv6)

`CLOUDINARY_URL` and `DATABASE_URL` are already supported in `config.py`, and `flask db upgrade` runs automatically as the release command. Feed caching now uses a simple in-memory store and works without additional services.

### Background tasks

Feed items are inserted synchronously using an in-memory queue, so no external
worker is required. Additional maintenance jobs run with
[`apscheduler`](https://apscheduler.readthedocs.io/) when the environment
variable `SCHEDULER=1`.

### Respaldo de base de datos

Al activar el scheduler se ejecuta semanalmente un respaldo de la base de
datos mediante `pg_dump`. El archivo resultante se sube a S3 si defines:

```bash
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
BACKUP_BUCKET=nombre-del-bucket
```

Opcionalmente puedes establecer `BACKUP_PREFIX` para el directorio dentro del
bucket. Si `BACKUP_BUCKET` no está definido, las copias se guardan localmente en
`BACKUP_DIR` (por defecto `backups/`).

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

## Mi Espacio Personal

El panel "Mi Espacio Personal" te permite organizar tareas, metas y notas en un
tablero privado. Actívalo visitando `/espacio-personal` y presionando el botón
**Comenzar** para crear tu primer bloque. Puedes añadir distintos tipos de
bloques y ordenarlos mediante *drag and drop*:

- **Bitácora Inteligente** (`nota`)
- **Tablero Kanban** (`kanban`)
- **Objetivo Académico** (`objetivo`)
- **Tarea Individual** (`tarea`)
- **Lista de Tareas** (`lista`)
- **Recordatorio** (`recordatorio`)
- **Frase Motivacional** (`frase`)
- **Enlace Educativo** (`enlace`)
- **Bloque Personalizado** (`bloque`)

El tablero incluye un *modo enfoque* que oculta la navegación y barras laterales
para eliminar distracciones. Haz clic en **Modo Enfoque** para activarlo (aparece
un botón flotante para salir). Algunos atajos de teclado disponibles son:

- <kbd>Shift</kbd> + <kbd>H</kbd> – Ir al inicio
- <kbd>Shift</kbd> + <kbd>N</kbd> – Nueva publicación
- <kbd>Shift</kbd> + <kbd>Q</kbd> – Notas rápidas

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
La variable `ENABLE_CSRF` está siempre activa en producción y no deberías deshabilitarla.
En producción la protección CSRF está siempre habilitada.

Si necesitas el token desde JavaScript puedes leerlo con:

```javascript
document.querySelector('meta[name="csrf-token"]').content;
```

### Error Monitoring

To capture errors with [Sentry](https://sentry.io/), set the `SENTRY_DSN` environment variable. Additional options `SENTRY_ENVIRONMENT` and `SENTRY_TRACES_RATE` can fine-tune alerts and performance sampling. See `docs/error_monitoring.md` for details.
## Visor de PDF integrado (PDF.js)

Desde el commit `Load PDF.js locally`, CRUNEVO utiliza una versión local de PDF.js para visualizar apuntes PDF directamente en el navegador. Esto evita errores por bloqueo de red al cargar desde CDNs y mejora la compatibilidad con Cloudinary.

Ubicación:
- `static/pdfjs/pdf.min.js`
- `static/pdfjs/pdf.worker.min.js`
