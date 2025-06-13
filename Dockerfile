FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el archivo alembic.ini a /app/migrations
COPY alembic.ini /app/migrations/alembic.ini

# Copiamos el código fuente
COPY crunevo /app/crunevo
COPY migrations /app/migrations

# Línea corregida para corregir el fallo del servidor en Fly.io
CMD ["gunicorn", "-b", "0.0.0.0:8080", "crunevo.wsgi:app"]
