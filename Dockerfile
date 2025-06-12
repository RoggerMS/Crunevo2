FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY crunevo /app/crunevo
COPY migrations /app/migrations  # ← Aquí falla si está vacía

CMD ["gunicorn", "-b", "0.0.0.0:8080", "crunevo.wsgi:app"]
