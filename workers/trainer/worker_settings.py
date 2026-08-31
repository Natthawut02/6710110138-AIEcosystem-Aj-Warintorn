"""
worker_settings.py (Trainer Worker)
-------------------------------------
ตั้งค่า ARQ Worker สำหรับ Trainer Worker โดยเฉพาะ
queue_name = "training_queue" ต้องตรงกับที่ backend/routers/train.py ใช้ตอน enqueue

รันด้วยคำสั่ง: arq worker_settings.WorkerSettings
"""

import os
from arq.connections import RedisSettings

from train_job import train_token_classification

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))


class WorkerSettings:
    redis_settings = RedisSettings(host=REDIS_HOST, port=REDIS_PORT)
    queue_name = "training_queue"
    functions = [train_token_classification]
    job_timeout = 3600
    max_jobs = 1
