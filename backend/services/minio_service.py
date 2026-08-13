"""
MinIO Object Storage Service.
Encapsulates MinIO Python SDK operations: bucket provisioning, versioning, upload, download, and listing.
"""

import io
from typing import List, Optional, Tuple, BinaryIO
from minio import Minio
from minio.error import S3Error
from minio.versioningconfig import VersioningConfig
from core.config import settings
from core.logger import get_logger
from schemas.storage import ObjectInfo, ObjectVersionInfo, UploadResponse, BucketInfo

logger = get_logger(__name__)


class MinioService:
    """Service wrapper managing MinIO client lifecycle and storage operations."""

    def __init__(self):
        self._client: Optional[Minio] = None

    def get_client(self) -> Minio:
        """Lazily initialize and return MinIO client instance."""
        if self._client is None:
            logger.debug(f"Initializing MinIO client connection to endpoint: {settings.MINIO_ENDPOINT}")
            self._client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=False
            )
        return self._client

    def ensure_bucket(self, bucket_name: Optional[str] = None) -> str:
        """Check if bucket exists; if not, create it."""
        client = self.get_client()
        target_bucket = bucket_name or settings.MINIO_BUCKET
        try:
            if not client.bucket_exists(target_bucket):
                logger.info(f"Bucket '{target_bucket}' does not exist. Creating bucket...")
                client.make_bucket(target_bucket)
                logger.info(f"Bucket '{target_bucket}' created successfully.")
            return target_bucket
        except S3Error as e:
            logger.error(f"MinIO S3Error while ensuring bucket '{target_bucket}': {e}")
            raise

    def set_versioning(self, bucket_name: Optional[str] = None, enable: bool = True) -> bool:
        """Enable or suspend versioning on the specified bucket."""
        client = self.get_client()
        target_bucket = self.ensure_bucket(bucket_name)
        status_str = "Enabled" if enable else "Suspended"
        try:
            client.set_bucket_versioning(target_bucket, VersioningConfig(status_str))
            logger.info(f"Bucket '{target_bucket}' versioning state changed to: {status_str}")
            return True
        except S3Error as e:
            logger.error(f"Failed to set versioning for bucket '{target_bucket}': {e}")
            raise

    def get_versioning_status(self, bucket_name: Optional[str] = None) -> bool:
        """Retrieve current bucket versioning configuration."""
        client = self.get_client()
        target_bucket = self.ensure_bucket(bucket_name)
        try:
            config = client.get_bucket_versioning(target_bucket)
            return config.status == "Enabled"
        except S3Error as e:
            logger.warning(f"Could not check versioning status on '{target_bucket}': {e}")
            return False

    def list_buckets(self) -> List[BucketInfo]:
        """List all buckets in the MinIO instance."""
        client = self.get_client()
        try:
            buckets = client.list_buckets()
            result = []
            for b in buckets:
                versioning = self.get_versioning_status(b.name)
                result.append(BucketInfo(
                    name=b.name,
                    creation_date=b.creation_date,
                    versioning_enabled=versioning
                ))
            return result
        except S3Error as e:
            logger.error(f"Failed to list buckets: {e}")
            raise

    def upload_stream(
        self,
        file_stream: BinaryIO,
        object_name: str,
        content_type: str,
        size: int,
        bucket_name: Optional[str] = None
    ) -> UploadResponse:
        """Upload a file stream into MinIO."""
        client = self.get_client()
        target_bucket = self.ensure_bucket(bucket_name)
        try:
            result = client.put_object(
                bucket_name=target_bucket,
                object_name=object_name,
                data=file_stream,
                length=size,
                content_type=content_type
            )
            logger.info(f"Successfully uploaded '{object_name}' (version_id: {result.version_id}) to '{target_bucket}'")
            return UploadResponse(
                bucket_name=target_bucket,
                object_name=object_name,
                version_id=result.version_id,
                size=size,
                content_type=content_type,
                url=f"http://{settings.MINIO_ENDPOINT}/{target_bucket}/{object_name}"
            )
        except S3Error as e:
            logger.error(f"Failed to upload object '{object_name}' to bucket '{target_bucket}': {e}")
            raise

    def list_objects(self, bucket_name: Optional[str] = None, prefix: str = "") -> List[ObjectInfo]:
        """List objects in bucket matching prefix."""
        client = self.get_client()
        target_bucket = self.ensure_bucket(bucket_name)
        try:
            objects = client.list_objects(target_bucket, prefix=prefix, recursive=True)
            res = []
            for obj in objects:
                res.append(ObjectInfo(
                    bucket_name=target_bucket,
                    object_name=obj.object_name,
                    size=obj.size,
                    last_modified=obj.last_modified,
                    content_type=obj.content_type if hasattr(obj, "content_type") else None,
                    version_id=getattr(obj, "version_id", None)
                ))
            return res
        except S3Error as e:
            logger.error(f"Failed to list objects in '{target_bucket}': {e}")
            raise

    def list_object_versions(self, object_name: str, bucket_name: Optional[str] = None) -> List[ObjectVersionInfo]:
        """List all version revisions for a given object."""
        client = self.get_client()
        target_bucket = self.ensure_bucket(bucket_name)
        try:
            objects = client.list_objects(target_bucket, prefix=object_name, include_version=True)
            versions = []
            for obj in objects:
                if obj.object_name == object_name:
                    versions.append(ObjectVersionInfo(
                        version_id=obj.version_id,
                        size=obj.size,
                        last_modified=obj.last_modified,
                        is_latest=getattr(obj, "is_latest", False),
                        etag=obj.etag
                    ))
            return versions
        except S3Error as e:
            logger.error(f"Failed to list versions for object '{object_name}': {e}")
            raise

    def download_object(
        self, 
        object_name: str, 
        bucket_name: Optional[str] = None, 
        version_id: Optional[str] = None
    ) -> Tuple[bytes, str]:
        """Download object content bytes along with its content-type."""
        client = self.get_client()
        target_bucket = self.ensure_bucket(bucket_name)
        try:
            response = client.get_object(target_bucket, object_name, version_id=version_id)
            content_type = response.headers.get("content-type", "application/octet-stream")
            data = response.read()
            response.close()
            response.release_conn()
            return data, content_type
        except S3Error as e:
            logger.error(f"Failed to download object '{object_name}' (version={version_id}): {e}")
            raise

    def delete_object(
        self, 
        object_name: str, 
        bucket_name: Optional[str] = None, 
        version_id: Optional[str] = None
    ) -> bool:
        """Delete an object or specific version from MinIO."""
        client = self.get_client()
        target_bucket = self.ensure_bucket(bucket_name)
        try:
            client.remove_object(target_bucket, object_name, version_id=version_id)
            logger.info(f"Deleted object '{object_name}' (version={version_id}) from '{target_bucket}'")
            return True
        except S3Error as e:
            logger.error(f"Failed to delete object '{object_name}': {e}")
            raise


# Global singleton instance
minio_service = MinioService()
