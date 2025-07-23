FROM python:3.11-slim

# Instalar dependencias necesarias
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requerimientos
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar alembic.ini en la ubicación correcta
COPY migrations/alembic.ini /app/migrations/alembic.ini

# Copiar código y migraciones
COPY crunevo /app/crunevo
COPY migrations /app/migrations
COPY migrations/versions /app/migrations/versions

# Ejecutar aplicación
# Run gunicorn using the FLASK_APP environment variable. Default to the
# public instance if FLASK_APP is not set (e.g. during local builds).
# Ejecuta la app usando el valor de FLASK_APP o usa wsgi:app por defecto
# Use eventlet worker for WebSocket support
CMD ["sh", "-c", "exec gunicorn --timeout 120 -k eventlet -b 0.0.0.0:8080 ${FLASK_APP:-crunevo.wsgi:app}"]
