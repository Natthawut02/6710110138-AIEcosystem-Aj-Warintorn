"""
Pydantic schemas for System Health and Component Diagnostics.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ComponentHealth(BaseModel):
    """Health check status for an individual system component."""
    name: str = Field(..., description="Name of the component", examples=["PostgreSQL", "Redis", "MinIO", "Label Studio"])
    status: str = Field(..., description="Health status (healthy, degraded, unreachable)", examples=["healthy"])
    latency_ms: Optional[float] = Field(None, description="Roundtrip check latency in milliseconds", examples=[3.45])
    details: Optional[Dict[str, Any]] = Field(None, description="Diagnostic metadata (e.g. version, active connections)")


class SystemHealthResponse(BaseModel):
    """Aggregated health status of the entire backend system and infrastructure components."""
    status: str = Field(..., description="Overall status (healthy, degraded, unhealthy)", examples=["healthy"])
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp of the diagnostic check")
    environment: str = Field("development", description="Deployment environment (development, staging, production)")
    components: Dict[str, ComponentHealth] = Field(..., description="Component-level health check breakdown")
