FROM python:3.11-slim

# Instalar dependencias necesarias para compilar paquetes como psycopg2
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar e instalar requerimientos
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar alembic.ini a la raíz como lo requiere Alembic
COPY migrations/alembic.ini /app/alembic.ini

# Copiar código fuente y migraciones
COPY crunevo /app/crunevo
COPY migrations /app/migrations
COPY migrations/versions /app/migrations/versions

# Ejecutar la aplicación con Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "crunevo.wsgi:app"]
