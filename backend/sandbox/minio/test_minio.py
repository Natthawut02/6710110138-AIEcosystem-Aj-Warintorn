import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from minio import Minio
from core.config import settings

def get_client():
    """สร้าง client เชื่อมต่อ MinIO server"""
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=False
    )

def enable_versioning(bucket_name):
    """เปิดใช้งาน versioning ให้ bucket"""
    client = get_client()
    from minio.versioningconfig import VersioningConfig
    client.set_bucket_versioning(bucket_name, VersioningConfig("Enabled"))
    print(f"Versioning enabled for bucket: {bucket_name}")

def upload_file(local_path, object_name):
    """อัปโหลดไฟล์ขึ้น MinIO คืนค่า version_id ที่ได้"""
    client = get_client()
    result = client.fput_object(settings.MINIO_BUCKET, object_name, local_path)
    print(f"Uploaded {object_name} - version_id: {result.version_id}")
    return result.version_id

def list_object_versions(object_name):
    """แสดงรายการ version ทั้งหมดของ object"""
    client = get_client()
    objects = client.list_objects(settings.MINIO_BUCKET, prefix=object_name, include_version=True)
    for obj in objects:
        print(f"version_id={obj.version_id} | last_modified={obj.last_modified} | is_latest={obj.is_latest}")

def download_file(object_name, save_path, version_id=None):
    """ดาวน์โหลดไฟล์ ถ้าระบุ version_id จะดึงเวอร์ชันนั้น ถ้าไม่ระบุจะได้เวอร์ชันล่าสุด"""
    client = get_client()
    client.fget_object(settings.MINIO_BUCKET, object_name, save_path, version_id=version_id)
    print(f"Downloaded {object_name} (version={version_id or 'latest'}) -> {save_path}")
