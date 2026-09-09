"""
API Routers Package.
Centralized exports for all modular route definitions.
"""

from routers.health import router as health_router
from routers.students import router as students_router
from routers.storage import router as storage_router
from routers.jobs import router as jobs_router
from routers.train import router as train_router
from routers.labeling import router as labeling_router
from routers.predict import router as predict_router

__all__ = [
    "health_router",
    "students_router",
    "storage_router",
    "jobs_router",
    "train_router",
    "labeling_router",
    "predict_router",
]
