"""
Pydantic schemas for Label Studio integration.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class LabelStudioProject(BaseModel):
    """Information regarding a Label Studio annotation project."""
    id: int = Field(..., description="Unique Project ID in Label Studio", examples=[1])
    title: str = Field(..., description="Title of the project", examples=["Image Classification - AI Ecosystem"])
    description: Optional[str] = Field(None, description="Detailed project description", examples=["Annotate bounding boxes and classes"])
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    task_number: Optional[int] = Field(0, description="Total number of tasks imported in project")
    total_annotations_number: Optional[int] = Field(0, description="Total completed annotations")


class LabelStudioTask(BaseModel):
    """Information regarding a single annotation task."""
    id: int = Field(..., description="Unique task identifier in Label Studio", examples=[101])
    project_id: int = Field(..., description="ID of parent project", examples=[1])
    data: Dict[str, Any] = Field(
        ..., 
        description="Task payload containing image URLs, text strings, or metadata to annotate",
        examples=[{"image": "http://localhost:9000/my-photos/sample.jpg", "caption": "Dataset image #1"}]
    )
    annotations: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="List of submitted annotations")
    created_at: Optional[str] = Field(None, description="Task creation timestamp")


class CreateTaskRequest(BaseModel):
    """Schema for pushing a new annotation task into Label Studio."""
    data: Dict[str, Any] = Field(
        ..., 
        description="Payload data for annotation (e.g. image URL or text string)",
        examples=[{"image": "http://localhost:9000/my-photos/image1.png"}]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {
                    "image": "http://localhost:9000/my-photos/image1.png",
                    "source": "MinIO S3",
                    "category": "Computer Vision"
                }
            }
        }
    )
