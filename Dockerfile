FROM python:3.11-slim

WORKDIR /app

# Copiar dependencias e instalarlas
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo lo necesario
COPY . .            # Copia todo el proyecto
COPY migrations/ /app/migrations/  # Asegura que migrations se copie

# Ejecutar Gunicorn como servidor
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
