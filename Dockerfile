FROM python:3.11-slim

# Instalar dependencias necesarias
RUN apt-get update && apt-get install -y build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

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

# Crear directorio para instancia
RUN mkdir -p /app/instance

# Variables de entorno
ENV FLASK_APP=crunevo.wsgi:app
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Exponer puerto
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/healthz || exit 1

# Ejecutar aplicación
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "60", "--keep-alive", "2", "--max-requests", "1000", "--max-requests-jitter", "100", "--preload", "crunevo.wsgi:app"]
