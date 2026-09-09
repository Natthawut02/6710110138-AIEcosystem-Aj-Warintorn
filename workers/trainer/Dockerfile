FROM ajnt-trainer-worker:latest

WORKDIR /app

RUN pip install --no-cache-dir mlflow-skinny==2.16.2 boto3==1.35.24

COPY . .

RUN mkdir -p /app/logs

ENV LOG_DIR=/app/logs
ENV PYTHONUNBUFFERED=1

CMD ["python3", "-m", "arq", "worker_settings.WorkerSettings"]
