FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3.11 python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --default-timeout=1000 --retries 10 --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/logs

ENV LOG_DIR=/app/logs
ENV PYTHONUNBUFFERED=1

CMD ["python3", "-m", "arq", "worker_settings.WorkerSettings"]
