FROM python:3.11-slim

RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .  

COPY crunevo /app/crunevo
COPY migrations /app/migrations

CMD ["gunicorn", "-b", "0.0.0.0:8080", "crunevo.wsgi:app"]
