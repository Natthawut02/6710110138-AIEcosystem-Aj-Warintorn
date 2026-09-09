FROM ajnt-inference-worker:latest

WORKDIR /app

RUN pip install --no-cache-dir pandas

COPY . .

RUN mkdir -p /app/logs

ENV PYTHONUNBUFFERED=1
ENV LOG_DIR=/app/logs

CMD ["python", "-m", "arq", "worker_settings.WorkerSettings"]
