"""
ARQ / Redis Background Job Service.
Manages asynchronous task queuing and inspection with Redis.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from arq.connections import create_pool, RedisSettings, ArqRedis
from arq.jobs import Job, JobStatus
from core.config import settings
from core.logger import get_logger
from schemas.job import JobInfo

logger = get_logger(__name__)


class JobService:
    """Service wrapper for interacting with ARQ Redis Job Queue."""

    def __init__(self):
        self._pool: Optional[ArqRedis] = None

    async def get_pool(self) -> ArqRedis:
        """Lazily initialize and return ARQ Redis pool connection."""
        if self._pool is None:
            logger.debug(f"Connecting to Redis ARQ pool at {settings.REDIS_HOST}:{settings.REDIS_PORT}...")
            redis_settings = RedisSettings(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT
            )
            self._pool = await create_pool(redis_settings)
        return self._pool

    async def enqueue_job(
        self,
        job_name: str = "simple_work",
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None
    ) -> JobInfo:
        """Enqueue an asynchronous job to Redis."""
        pool = await self.get_pool()
        args = args or []
        kwargs = kwargs or {}

        try:
            job = await pool.enqueue_job(job_name, *args, **kwargs)
            logger.info(f"Enqueued ARQ job '{job_name}' with ID {job.job_id}")
            return JobInfo(
                job_id=job.job_id,
                job_name=job_name,
                status="queued",
                enqueued_at=datetime.utcnow(),
                result=None,
                success=None
            )
        except Exception as e:
            logger.error(f"Failed to enqueue job '{job_name}': {e}")
            raise

    async def get_job_status(self, job_id: str) -> JobInfo:
        """Check status and retrieve results of a previously enqueued job."""
        pool = await self.get_pool()
        job = Job(job_id=job_id, redis=pool)
        status = await job.status()
        
        status_str = status.value if hasattr(status, "value") else str(status)
        result = None
        success = None
        
        if status == JobStatus.complete:
            try:
                info = await job.result_info()
                result = info.result if info else None
                success = info.success if info else True
            except Exception as e:
                logger.warning(f"Could not read result info for job {job_id}: {e}")
                result = str(e)
                success = False

        return JobInfo(
            job_id=job_id,
            job_name="unknown",
            status=status_str,
            enqueued_at=None,
            result=result,
            success=success
        )

    async def close(self):
        """Gracefully close Redis pool connection."""
        if self._pool is not None:
            logger.info("Closing ARQ Redis connection pool...")
            await self._pool.close()
            self._pool = None


# Global singleton instance
job_service = JobService()
