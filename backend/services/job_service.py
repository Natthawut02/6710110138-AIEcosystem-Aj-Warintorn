"""
ARQ / Redis Background Job Service.
Manages asynchronous task queuing and inspection with Redis.

*** อัปเดตสำหรับ WTN-A07 ***
เพิ่ม 2 ความสามารถใหม่ใน enqueue_job():
1. defer_until   -> ส่งต่อเป็น _defer_until ให้ ARQ เพื่อ "ตั้งเวลาเริ่มงานล่วงหน้า"
                    (ตรงกับที่โจทย์ระบุว่า Add train queue time)
2. queue_name    -> ส่งต่อเป็น _queue_name ให้ ARQ เพื่อแยกคิวงานเทรน (training_queue)
                    ออกจากคิวงานทั่วไป (default queue) ทำให้ Trainer Worker (มี GPU)
                    เป็นตัวเดียวที่ดึงงานเทรนไปทำ ไม่ปนกับ Worker เบา ๆ ตัวอื่น
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
        kwargs: Optional[Dict[str, Any]] = None,
        defer_until: Optional[datetime] = None,
        queue_name: Optional[str] = None,
    ) -> JobInfo:
        """
        Enqueue an asynchronous job to Redis.

        defer_until: ถ้าระบุ จะสั่งให้ ARQ "เลื่อน" การเริ่มงานไปจนถึงเวลาที่กำหนด
                     (ARQ ยังคง enqueue job ทันที แต่ worker จะไม่หยิบไปทำจนกว่าจะถึงเวลานี้)
        queue_name:  ถ้าระบุ จะ enqueue เข้าคิวชื่อนี้แทนคิว default
                     ใช้แยกงานเทรน (ที่ต้องใช้ GPU) ออกจากงานเบา ๆ ทั่วไป
        """
        pool = await self.get_pool()
        args = args or []
        kwargs = kwargs or {}

        extra_arq_kwargs: Dict[str, Any] = {}
        if defer_until is not None:
            extra_arq_kwargs["_defer_until"] = defer_until
        if queue_name is not None:
            extra_arq_kwargs["_queue_name"] = queue_name

        try:
            job = await pool.enqueue_job(job_name, *args, **extra_arq_kwargs, **kwargs)
            logger.info(
                f"Enqueued ARQ job '{job_name}' with ID {job.job_id} "
                f"(queue={queue_name or 'default'}, defer_until={defer_until})"
            )
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

    async def get_job_status(self, job_id: str, queue_name: Optional[str] = None) -> JobInfo:
        """Check status and retrieve results of a previously enqueued job."""
        pool = await self.get_pool()
        job = Job(job_id=job_id, redis=pool, _queue_name=queue_name or "arq:queue")
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
