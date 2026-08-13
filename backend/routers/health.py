"""
Health & Diagnostic Endpoints.
Provides aggregated and component-level health checks for PostgreSQL, Redis, MinIO, and Label Studio.
"""

import time
import httpx
from fastapi import APIRouter, status
from sqlalchemy import text
from db.database import SessionLocal
from services.job_service import job_service
from services.minio_service import minio_service
from core.config import settings
from schemas.health import SystemHealthResponse, ComponentHealth
from schemas.common import ErrorResponse

router = APIRouter(
    prefix="/health",
    tags=["System Diagnostics"]
)


@router.get(
    "",
    response_model=SystemHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Multi-Component System Health Check",
    description="""
Evaluates the connectivity and latency across all core infrastructure components:
- **PostgreSQL Database**: Executes a lightweight verification query (`SELECT 1`).
- **Redis Cache & Queue**: Verifies connectivity via the ARQ Redis connection pool.
- **MinIO Object Storage**: Performs a bucket listing check to verify S3 storage accessibility.
- **Label Studio**: Tests HTTP connectivity against the configured Label Studio server endpoint.

Returns an aggregated status summary (`healthy`, `degraded`, or `unhealthy`) alongside detailed per-component metrics.
    """,
    response_description="Detailed multi-component health diagnostic summary",
    responses={
        200: {
            "description": "System health evaluation completed",
            "model": SystemHealthResponse
        },
        500: {
            "description": "Internal server error occurred during health inspection",
            "model": ErrorResponse
        }
    }
)
async def check_system_health():
    """Perform real-time round-trip diagnostic checks on all system dependencies."""
    components = {}
    overall_healthy = True

    # 1. PostgreSQL Check
    pg_start = time.perf_counter()
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        pg_latency = round((time.perf_counter() - pg_start) * 1000, 2)
        components["postgresql"] = ComponentHealth(
            name="PostgreSQL Database",
            status="healthy",
            latency_ms=pg_latency,
            details={"host": settings.POSTGRES_HOST, "database": settings.POSTGRES_DB}
        )
    except Exception as e:
        overall_healthy = False
        components["postgresql"] = ComponentHealth(
            name="PostgreSQL Database",
            status="unreachable",
            latency_ms=None,
            details={"error": str(e)}
        )

    # 2. Redis Check
    redis_start = time.perf_counter()
    try:
        pool = await job_service.get_pool()
        await pool.ping()
        redis_latency = round((time.perf_counter() - redis_start) * 1000, 2)
        components["redis"] = ComponentHealth(
            name="Redis Task Broker",
            status="healthy",
            latency_ms=redis_latency,
            details={"host": settings.REDIS_HOST, "port": settings.REDIS_PORT}
        )
    except Exception as e:
        overall_healthy = False
        components["redis"] = ComponentHealth(
            name="Redis Task Broker",
            status="unreachable",
            latency_ms=None,
            details={"error": str(e)}
        )

    # 3. MinIO Check
    minio_start = time.perf_counter()
    try:
        minio_service.get_client().list_buckets()
        minio_latency = round((time.perf_counter() - minio_start) * 1000, 2)
        components["minio"] = ComponentHealth(
            name="MinIO Object Storage",
            status="healthy",
            latency_ms=minio_latency,
            details={"endpoint": settings.MINIO_ENDPOINT, "default_bucket": settings.MINIO_BUCKET}
        )
    except Exception as e:
        overall_healthy = False
        components["minio"] = ComponentHealth(
            name="MinIO Object Storage",
            status="unreachable",
            latency_ms=None,
            details={"error": str(e)}
        )

    # 4. Label Studio Check
    ls_start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.LABEL_STUDIO_URL}/api/version")
            ls_latency = round((time.perf_counter() - ls_start) * 1000, 2)
            components["label_studio"] = ComponentHealth(
                name="Label Studio Annotation Engine",
                status="healthy" if resp.status_code < 500 else "degraded",
                latency_ms=ls_latency,
                details={"url": settings.LABEL_STUDIO_URL, "status_code": resp.status_code}
            )
    except Exception as e:
        overall_healthy = False
        components["label_studio"] = ComponentHealth(
            name="Label Studio Annotation Engine",
            status="unreachable",
            latency_ms=None,
            details={"error": str(e)}
        )

    return SystemHealthResponse(
        status="healthy" if overall_healthy else "degraded",
        components=components
    )
