"""
Pydantic schemas for MinIO Object Storage operations.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ObjectVersionInfo(BaseModel):
    """Information regarding a specific version of a MinIO object."""
    version_id: Optional[str] = Field(None, description="Unique version identifier assigned by MinIO", examples=["3e4f6a7b-1234-5678-90ab-cdef12345678"])
    size: int = Field(..., description="Size of the object in bytes", examples=[1048576])
    last_modified: Optional[datetime] = Field(None, description="Timestamp of when this version was created/updated")
    is_latest: bool = Field(True, description="Indicates if this is the active/latest version of the object")
    etag: Optional[str] = Field(None, description="ETag/MD5 checksum hash of the object")


class ObjectInfo(BaseModel):
    """Metadata information for an object stored in MinIO."""
    bucket_name: str = Field(..., description="Target bucket name", examples=["my-photos"])
    object_name: str = Field(..., description="Object name/path inside the bucket", examples=["datasets/images/sample.jpg"])
    size: int = Field(..., description="Object size in bytes", examples=[204800])
    last_modified: Optional[datetime] = Field(None, description="Last modification timestamp")
    content_type: Optional[str] = Field(None, description="MIME type of the stored object", examples=["image/jpeg"])
    version_id: Optional[str] = Field(None, description="Active version ID of the object")


class UploadResponse(BaseModel):
    """Response returned upon successful file upload to MinIO."""
    bucket_name: str = Field(..., description="Target bucket name", examples=["my-photos"])
    object_name: str = Field(..., description="Stored object path/name", examples=["photos/profile.png"])
    version_id: Optional[str] = Field(None, description="Assigned MinIO version ID (if versioning is enabled)", examples=["v1-abc-123"])
    size: int = Field(..., description="Uploaded file size in bytes", examples=[51200])
    content_type: str = Field(..., description="Detected MIME content type", examples=["image/png"])
    url: Optional[str] = Field(None, description="Presigned or direct access URL if applicable")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "bucket_name": "my-photos",
                "object_name": "photos/profile.png",
                "version_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                "size": 51200,
                "content_type": "image/png",
                "url": "http://localhost:9000/my-photos/photos/profile.png"
            }
        }
    )


class BucketInfo(BaseModel):
    """Details about a MinIO storage bucket."""
    name: str = Field(..., description="Name of the storage bucket", examples=["my-photos"])
    creation_date: Optional[datetime] = Field(None, description="Bucket creation timestamp")
    versioning_enabled: bool = Field(False, description="Whether versioning is currently enabled for this bucket")
