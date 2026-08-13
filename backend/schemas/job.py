"""
Pydantic schemas for ARQ / Redis background asynchronous jobs.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class JobCreate(BaseModel):
    """Schema for dispatching a new background job to ARQ / Redis queue."""
    job_name: str = Field(
        "simple_work", 
        description="Name of the registered worker function to execute",
        examples=["simple_work"]
    )
    args: List[Any] = Field(
        default_factory=list, 
        description="Positional arguments passed to the worker function",
        examples=[["Training Epoch 1", 100]]
    )
    kwargs: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Keyword arguments passed to the worker function",
        examples=[{"priority": "high", "notify": True}]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_name": "simple_work",
                "args": ["Verify Worker Pipeline", 42],
                "kwargs": {
                    "task_type": "MODEL_EVALUATION",
                    "dataset": "cifar-10",
                    "retries": 3
                }
            }
        }
    )


class JobInfo(BaseModel):
    """Status and metadata of an enqueued background job."""
    job_id: str = Field(..., description="Unique UUID assigned to the background job", examples=["e7b1a23c4d5e6f7a8b9c0d1e2f3a4b5c"])
    job_name: str = Field(..., description="Worker function executed", examples=["simple_work"])
    status: str = Field(..., description="Current lifecycle state (queued, in_progress, complete, not_found)", examples=["queued"])
    enqueued_at: Optional[datetime] = Field(None, description="Timestamp when job was placed into Redis queue")
    result: Optional[Any] = Field(None, description="Return value or output if the job has completed")
    success: Optional[bool] = Field(None, description="Whether the job finished successfully without unhandled exceptions")
