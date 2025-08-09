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

# Configuración de puerto
ENV PORT=8080
EXPOSE 8080

# Ejecutar aplicación
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "--threads", "8", "--timeout", "120", "--bind", "0.0.0.0:8080", "crunevo.wsgi:app"]
