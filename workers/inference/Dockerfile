FROM ajnt-inference-worker:latest

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/logs

ENV PYTHONUNBUFFERED=1
ENV LOG_DIR=/app/logs

CMD ["python", "-m", "arq", "worker_settings.WorkerSettings"]
