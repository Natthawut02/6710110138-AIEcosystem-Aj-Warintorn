"""
minio_client.py
-----------------
MinIO client แบบ self-contained สำหรับ Trainer Worker โดยเฉพาะ
(ไม่ import จากโค้ด backend/ เพราะ Trainer Worker รันเป็นคนละ Container กัน
ต้องพกพาตัวเองได้ ไม่พึ่งพา path หรือ module ของ service อื่น)
"""

import os
from typing import Optional
from minio import Minio
from minio.versioningconfig import VersioningConfig

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "password123")

_client: Optional[Minio] = None


def get_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False,
        )
    return _client


def ensure_bucket(bucket_name: str, enable_versioning: bool = False) -> None:
    client = get_client()
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
    if enable_versioning:
        client.set_bucket_versioning(bucket_name, VersioningConfig("Enabled"))


def download_file(bucket_name: str, object_name: str, local_path: str) -> None:
    client = get_client()
    client.fget_object(bucket_name, object_name, local_path)


def upload_file(bucket_name: str, object_name: str, local_path: str, content_type: str = "application/octet-stream") -> str:
    client = get_client()
    ensure_bucket(bucket_name, enable_versioning=True)
    result = client.fput_object(bucket_name, object_name, local_path, content_type=content_type)
    return result.version_id
