FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

#  Copiamos el archivo alembic.ini a /app
COPY alembic.ini /app/migrations/alembic.ini

# Copiamos el resto del código
COPY crunevo /app/crunevo
COPY migrations /app/migrations

CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
