"""
MinIO Object Storage & Versioning Endpoints.
Provides file upload, streaming download, bucket management, and version history exploration.
"""

import io
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, Query, Path, HTTPException, Response, status
from minio.error import S3Error
from services.minio_service import minio_service
from schemas.storage import ObjectInfo, ObjectVersionInfo, UploadResponse, BucketInfo
from schemas.common import StandardResponse, ErrorResponse

router = APIRouter(
    prefix="/storage",
    tags=["MinIO Object Storage"]
)


@router.get(
    "/buckets",
    response_model=List[BucketInfo],
    status_code=status.HTTP_200_OK,
    summary="List Storage Buckets",
    description="""
Lists all accessible buckets in the MinIO instance along with their creation timestamps and versioning status.
    """,
    response_description="List of available buckets in MinIO",
    responses={
        200: {"description": "Buckets retrieved successfully", "model": List[BucketInfo]},
        500: {"description": "S3 connection error", "model": ErrorResponse}
    }
)
def list_buckets():
    """Retrieve all MinIO buckets with versioning state."""
    try:
        return minio_service.list_buckets()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list MinIO buckets: {str(e)}"
        )


@router.post(
    "/buckets/{bucket_name}/versioning",
    response_model=StandardResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Configure Bucket Versioning",
    description="""
Enables or suspends S3 object versioning for the specified MinIO bucket.
When versioning is enabled, modifying or re-uploading an object creates a new version ID rather than overwriting existing data.
    """,
    response_description="Confirmation of bucket versioning status change",
    responses={
        200: {"description": "Bucket versioning configuration updated successfully"},
        500: {"description": "MinIO error setting versioning", "model": ErrorResponse}
    }
)
def configure_versioning(
    bucket_name: str = Path(..., description="Target bucket name", examples=["my-photos"]),
    enable: bool = Query(True, description="True to enable versioning, False to suspend", examples=[True])
):
    """Enable or suspend object versioning on a bucket."""
    try:
        minio_service.set_versioning(bucket_name=bucket_name, enable=enable)
        state_str = "enabled" if enable else "suspended"
        return StandardResponse(
            success=True,
            message=f"Versioning has been {state_str} for bucket '{bucket_name}'.",
            data={"bucket": bucket_name, "versioning_enabled": enable}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update bucket versioning: {str(e)}"
        )


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload File to MinIO",
    description="""
Uploads a binary file stream into MinIO S3 storage.

- **file**: Multipart file payload.
- **object_name**: Custom destination path inside bucket (optional, defaults to original filename).
- **bucket_name**: Target MinIO bucket (optional, defaults to configured `my-photos` bucket).

If bucket versioning is enabled, MinIO automatically attaches a unique `version_id` to the response.
    """,
    response_description="Metadata of the uploaded object including size and version_id",
    responses={
        201: {"description": "File uploaded successfully", "model": UploadResponse},
        400: {"description": "Invalid file or empty payload", "model": ErrorResponse},
        500: {"description": "MinIO upload failure", "model": ErrorResponse}
    }
)
async def upload_file(
    file: UploadFile = File(..., description="File content to store in MinIO"),
    object_name: Optional[str] = Form(None, description="Custom object path/name (e.g. photos/sample.png)"),
    bucket_name: Optional[str] = Form(None, description="Optional destination bucket name")
):
    """Upload a file to MinIO with version tracking."""
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided.")

    target_name = object_name or file.filename
    content = await file.read()
    size = len(content)
    content_type = file.content_type or "application/octet-stream"

    try:
        file_stream = io.BytesIO(content)
        result = minio_service.upload_stream(
            file_stream=file_stream,
            object_name=target_name,
            content_type=content_type,
            size=size,
            bucket_name=bucket_name
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload to MinIO failed: {str(e)}"
        )


@router.get(
    "/objects",
    response_model=List[ObjectInfo],
    status_code=status.HTTP_200_OK,
    summary="List Objects in Bucket",
    description="""
Retrieves the list of objects stored inside a MinIO bucket.
Supports filtering by object prefix (e.g. `datasets/images/`).
    """,
    response_description="List of stored objects with metadata",
    responses={
        200: {"description": "Objects listed successfully", "model": List[ObjectInfo]}
    }
)
def list_objects(
    bucket_name: Optional[str] = Query(None, description="Bucket to query (default: configured bucket)", examples=["my-photos"]),
    prefix: str = Query("", description="Object key prefix filter", examples=[""])
):
    """List objects in bucket with optional prefix filtering."""
    try:
        return minio_service.list_objects(bucket_name=bucket_name, prefix=prefix)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list objects: {str(e)}"
        )


@router.get(
    "/objects/{object_name:path}/versions",
    response_model=List[ObjectVersionInfo],
    status_code=status.HTTP_200_OK,
    summary="List Object Version History",
    description="""
Retrieves all historical version revisions for a given object key in MinIO.
Allows inspecting all previous revisions, their sizes, timestamps, and current active status.
    """,
    response_description="List of all version revisions for the specified object",
    responses={
        200: {"description": "Version history retrieved", "model": List[ObjectVersionInfo]},
        404: {"description": "Object not found", "model": ErrorResponse}
    }
)
def list_object_versions(
    object_name: str = Path(..., description="Object name or path (e.g. sample.png)", examples=["sample.png"]),
    bucket_name: Optional[str] = Query(None, description="Target bucket name", examples=["my-photos"])
):
    """Retrieve complete version history of an object."""
    try:
        versions = minio_service.list_object_versions(object_name=object_name, bucket_name=bucket_name)
        if not versions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No versions found for object '{object_name}'"
            )
        return versions
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query object versions: {str(e)}"
        )


@router.get(
    "/download/{object_name:path}",
    summary="Download Object File Stream",
    description="""
Streams an object's binary content directly from MinIO to the HTTP client.
Supports downloading a specific historical revision by supplying the `version_id` query parameter.
If `version_id` is omitted, the latest version is returned.
    """,
    response_description="Binary file stream with appropriate Content-Type header",
    responses={
        200: {
            "description": "File stream returned successfully",
            "content": {"application/octet-stream": {}}
        },
        404: {"description": "Object or specified version ID not found", "model": ErrorResponse}
    }
)
def download_file(
    object_name: str = Path(..., description="Object key to download", examples=["sample.png"]),
    bucket_name: Optional[str] = Query(None, description="Bucket containing object", examples=["my-photos"]),
    version_id: Optional[str] = Query(None, description="Optional specific version ID to fetch", examples=["v1"])
):
    """Stream object content from MinIO with optional version specification."""
    try:
        data, content_type = minio_service.download_object(
            object_name=object_name,
            bucket_name=bucket_name,
            version_id=version_id
        )
        return Response(content=data, media_type=content_type)
    except S3Error as e:
        if e.code in ("NoSuchKey", "NoSuchVersion"):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Object not found: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete(
    "/objects/{object_name:path}",
    response_model=StandardResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete Object or Specific Version",
    description="""
Deletes an object or a specific version ID from MinIO.
If `version_id` is specified, only that particular historical revision is deleted.
    """,
    response_description="Confirmation of object deletion",
    responses={
        200: {"description": "Object deleted successfully"},
        500: {"description": "MinIO deletion error", "model": ErrorResponse}
    }
)
def delete_object(
    object_name: str = Path(..., description="Object name to delete", examples=["sample.png"]),
    bucket_name: Optional[str] = Query(None, description="Bucket name", examples=["my-photos"]),
    version_id: Optional[str] = Query(None, description="Optional specific version ID to delete")
):
    """Delete an object or revision from MinIO."""
    try:
        minio_service.delete_object(object_name=object_name, bucket_name=bucket_name, version_id=version_id)
        return StandardResponse(
            success=True,
            message=f"Object '{object_name}' (version={version_id or 'latest'}) deleted successfully.",
            data={"object_name": object_name, "version_id": version_id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete object: {str(e)}"
        )
