FROM python:3.11-slim

WORKDIR /app

# Install system utilities and PostgreSQL client library
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install MLflow and cloud storage drivers
RUN pip install --no-cache-dir \
    mlflow==2.16.2 \
    psycopg2-binary==2.9.9 \
    boto3==1.35.24

COPY entrypoint.py /app/entrypoint.py

EXPOSE 5000

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "/app/entrypoint.py"]
