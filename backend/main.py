"""
AI Ecosystem Backend Service - FastAPI Application Entrypoint.

This application provides a unified RESTful API layer connecting all AI Ecosystem core components:
1. PostgreSQL Database (SQLAlchemy ORM + Student entities)
2. MinIO S3 Object Storage (File streaming & Object Versioning)
3. Redis & ARQ Background Task Broker (Asynchronous processing)
4. Label Studio Integration (Data Annotation Management)
5. Custom Logging & Diagnostic Health Suite
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from core.config import settings
from core.logger import get_logger
from db.database import engine, Base
from services.job_service import job_service
from services.minio_service import minio_service
from routers import (
    health_router,
    students_router,
    storage_router,
    jobs_router,
    train_router,
    labeling_router,
    predict_router
)

logger = get_logger("main")


# ==============================================================================
# 1. OpenAPI Tags Metadata Definition (FastAPI Metadata Tutorial)
# ==============================================================================
tags_metadata = [
    {
        "name": "System Diagnostics",
        "description": "Real-time health monitoring and latency diagnostics across PostgreSQL, Redis, MinIO, and Label Studio.",
        "externalDocs": {
            "description": "System Architecture Overview",
            "url": "https://fastapi.tiangolo.com/advanced/custom-response/",
        },
    },
    {
        "name": "Student Management",
        "description": "PostgreSQL database CRUD operations using SQLAlchemy ORM for student records management.",
    },
    {
        "name": "MinIO Object Storage",
        "description": "S3-compatible Object Storage management supporting multi-part file uploads, object versioning, and binary streaming.",
        "externalDocs": {
            "description": "MinIO Python SDK Docs",
            "url": "https://min.io/docs/minio/linux/developers/python/API.html",
        },
    },
    {
        "name": "Async Task & Worker Queue",
        "description": "Asynchronous job scheduling and status tracking backed by Redis and ARQ worker framework.",
        "externalDocs": {
            "description": "ARQ Job Queue Documentation",
            "url": "https://arq-docs.helpmanual.io/",
        },
    },
    {
        "name": "Label Studio Integration",
        "description": "Data annotation integration for AI dataset pipelines connecting to Label Studio.",
        "externalDocs": {
            "description": "Label Studio API Docs",
            "url": "https://labelstud.io/guide/api.html",
        },
    },
    {
        "name": "Trainer Worker",
        "description": "Asynchronous model training and dedicated GPU worker queue management.",
    },
    {
        "name": "Inference & Prediction",
        "description": "WTN-A08: MLflow and Inference Worker implementation for Named Entity Recognition (NER).",
    },
]


# ==============================================================================
# 2. Application Lifespan Context Manager (Startup & Shutdown)
# ==============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events cleanly.
    - Startup: Creates database tables, ensures MinIO bucket exists, logs system initialization.
    - Shutdown: Closes Redis connection pools and cleans up resources.
    """
    logger.info("=" * 60)
    logger.info(f"Starting {settings.APP_NAME} (Debug={settings.DEBUG})...")
    
    # 1. Initialize PostgreSQL Tables
    try:
        logger.info("Initializing PostgreSQL database schema...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"PostgreSQL initialization warning: {e}")

    # 2. Ensure MinIO Buckets
    try:
        for b in [settings.MINIO_BUCKET, "datasets", "models", "mlflow"]:
            minio_service.ensure_bucket(b)
        logger.info("All required MinIO buckets (my-photos, datasets, models, mlflow) are ready.")
    except Exception as e:
        logger.warning(f"MinIO bucket check warning: {e}")

    logger.info(f"{settings.APP_NAME} initialization completed successfully!")
    logger.info("=" * 60)

    yield

    # Graceful Shutdown
    logger.info("Shutting down application and closing resource pools...")
    await job_service.close()
    logger.info("Application shutdown complete.")


# ==============================================================================
# 3. FastAPI Application Initialization with Full Metadata
# ==============================================================================
app = FastAPI(
    title="AI Ecosystem Core Backend API",
    summary="Unified RESTful API Suite for AI Data Pipelines, Storage, Database, and Worker Tasks",
    description="""
# AI Ecosystem Backend Service 🚀

Welcome to the **AI Ecosystem Backend API** documentation. This service serves as the core orchestration backend for the AI platform.

---

### 🧩 Connected Components:
* **🐘 PostgreSQL Database**: Structured data storage and ORM model persistence.
* **📦 MinIO Object Storage**: S3-compatible file storage with object versioning.
* **⚡ Redis & ARQ Worker**: High-performance asynchronous background task queue.
* **🏷️ Label Studio**: Human-in-the-loop dataset annotation and task management.
* **📊 Centralized Logger & Diagnostics**: Live system health inspection.

---

### 📚 Documentation & Schema Endpoints:
* **Interactive Swagger UI**: [`/docs`](/docs)
* **ReDoc Interactive Documentation**: [`/redoc`](/redoc)
* **Raw OpenAPI Specification (JSON)**: [`/openapi.json`](/openapi.json)
    """,
    version="1.0.0",
    terms_of_service="https://example.com/terms/",
    contact={
        "name": "AI Ecosystem Development Team",
        "url": "https://github.com/Natthawut02/6710110138-AIEcosystem-Aj-Warintorn",
        "email": "natthawut@example.com",
    },
    license_info={
        "name": "MIT License",
        "identifier": "MIT",
    },
    openapi_tags=tags_metadata,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan
)


# ==============================================================================
# 3.1 Interactive Documentation Endpoints (Reliable CDN)
# ==============================================================================
from fastapi.openapi.docs import get_redoc_html

@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    """Custom ReDoc UI route using official high-speed Redocly standalone CDN."""
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"
    )


# ==============================================================================
# 4. Middleware Configuration
# ==============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware for structured request/response duration logging."""
    import time
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    logger.info(f"{request.method} {request.url.path} -> Status {response.status_code} ({duration_ms}ms)")
    return response


# ==============================================================================
# 5. Router Registration
# ==============================================================================
API_V1_PREFIX = "/api/v1"

app.include_router(health_router, prefix=API_V1_PREFIX)
app.include_router(students_router, prefix=API_V1_PREFIX)
app.include_router(storage_router, prefix=API_V1_PREFIX)
app.include_router(jobs_router, prefix=API_V1_PREFIX)
app.include_router(labeling_router, prefix=API_V1_PREFIX)
app.include_router(train_router, prefix=API_V1_PREFIX)
app.include_router(predict_router, prefix=API_V1_PREFIX)
# Also register directly at root so /predict and /inference work as specified in assignment diagram
app.include_router(predict_router)


# ==============================================================================
# 6. Service Discovery Root Endpoint
# ==============================================================================
@app.get(
    "/",
    tags=["System Diagnostics"],
    summary="API Discovery & Welcome Root",
    description="Returns high-level metadata, version information, and quick links to interactive documentation."
)
def root_discovery():
    """Service discovery endpoint providing quick navigational links."""
    return {
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "status": "online",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json"
        },
        "endpoints": {
            "health": f"{API_V1_PREFIX}/health",
            "students": f"{API_V1_PREFIX}/students",
            "storage": f"{API_V1_PREFIX}/storage",
            "jobs": f"{API_V1_PREFIX}/jobs",
            "labeling": f"{API_V1_PREFIX}/labeling",
            "train": f"{API_V1_PREFIX}/train"
        }
    }


# ==============================================================================
# 7. Local Development Server Launcher
# ==============================================================================
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
