FROM python:3.11-slim

# Instala dependencias del sistema necesarias
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo
WORKDIR /app

# Copia e instala los requisitos
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copia el archivo alembic.ini (corregida ubicación)
COPY alembic.ini .  # ← Va a /app (NO a /app/migrations)

# Copia el código fuente y migraciones
COPY crunevo /app/crunevo
COPY migrations /app/migrations

# Comando para ejecutar Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "crunevo.wsgi:app"]
