"""
worker_settings.py (Inference Worker)
--------------------------------------
ตั้งค่า ARQ Worker สำหรับ Inference Worker
queue_name = "inference_queue" ตรงกับที่ backend/routers/predict.py ใช้งาน

รันด้วยคำสั่ง: arq worker_settings.WorkerSettings
"""

import os
from arq.connections import RedisSettings
from inference_job import predict_token_classification, startup, shutdown

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))


class WorkerSettings:
    redis_settings = RedisSettings(host=REDIS_HOST, port=REDIS_PORT)
    queue_name = "inference_queue"
    functions = [predict_token_classification]
    on_startup = startup
    on_shutdown = shutdown
    job_timeout = 300
    max_jobs = 10
