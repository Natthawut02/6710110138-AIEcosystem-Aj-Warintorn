"""
ARQ Worker configuration settings.
This file defines the worker functions and connection settings for ARQ background tasks.
"""

from arq.connections import RedisSettings
from core.config import settings

async def simple_work(ctx: dict, *args, **kwargs) -> str:
    """
    A simple background job that prints received data and returns a confirmation message.
    """
    print(f"[ARQ Job: simple_work] Received job data - args: {args}, kwargs: {kwargs}")
    return f"Success: simple_work completed with args={args} and kwargs={kwargs}"

class WorkerSettings:
    """
    Configuration class for ARQ Worker.
    Uses settings from core.config for Redis configuration.
    """
    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT
    )
    functions = [simple_work]
