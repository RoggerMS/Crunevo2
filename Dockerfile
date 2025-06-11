FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY crunevo /app/crunevo

ENV FLASK_APP=crunevo.app

CMD ["gunicorn", "-b", "0.0.0.0:8080", "crunevo.app:app"]
