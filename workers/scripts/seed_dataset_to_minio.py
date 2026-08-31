"""
seed_dataset_to_minio.py
-------------------------
สคริปต์นี้ใช้รัน "ครั้งเดียว" ก่อนเริ่มใช้งานระบบเทรน เพื่อดึง Dataset จาก Hugging Face
แล้วอัปโหลดเก็บไว้ใน MinIO ไว้ล่วงหน้า (ตามข้อ 4 ของโจทย์ WTN-A07)

Dataset ที่ใช้: conll2003 (มาตรฐานสำหรับงาน Token Classification / Named Entity Recognition
ตาม HuggingFace LLM Course บทที่ 7 ที่โจทย์อ้างอิงไว้:
https://huggingface.co/learn/llm-course/en/chapter7/2)

วิธีรัน:
    python seed_dataset_to_minio.py

ต้องตั้งค่า environment variables ให้ตรงกับ MinIO ที่รันอยู่ (ดู .env.example)
"""

import io
import json
import os
import sys

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from datasets import load_dataset
from minio import Minio
from minio.error import S3Error

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "password123")
DATASET_BUCKET = os.getenv("DATASET_BUCKET", "datasets")

DATASET_NAME = "conll2003"


def get_minio_client() -> Minio:
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,
    )


def ensure_bucket(client: Minio, bucket_name: str) -> None:
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        print(f"✅ สร้าง bucket '{bucket_name}' สำเร็จ")


def upload_split_as_jsonl(client: Minio, split_name: str, dataset_split) -> str:
    buffer = io.BytesIO()
    for row in dataset_split:
        buffer.write((json.dumps(row) + "\n").encode("utf-8"))
    buffer.seek(0)
    size = buffer.getbuffer().nbytes

    object_name = f"{DATASET_NAME}/{split_name}.jsonl"
    client.put_object(
        bucket_name=DATASET_BUCKET,
        object_name=object_name,
        data=buffer,
        length=size,
        content_type="application/jsonl",
    )
    print(f"✅ อัปโหลด {object_name} ({size:,} bytes, {len(dataset_split)} rows) สำเร็จ")
    return object_name


def main():
    print(f"กำลังดาวน์โหลด dataset '{DATASET_NAME}' จาก Hugging Face ...")
    try:
        dataset = load_dataset(DATASET_NAME, trust_remote_code=True)
    except Exception:
        dataset = load_dataset(f"eriktks/{DATASET_NAME}", trust_remote_code=True)

    client = get_minio_client()

    try:
        ensure_bucket(client, DATASET_BUCKET)

        object_names = []
        for split_name in dataset.keys():
            object_name = upload_split_as_jsonl(client, split_name, dataset[split_name])
            object_names.append(object_name)

        print("\n🎉 นำเข้า Dataset เข้า MinIO สำเร็จทั้งหมด")
        print("   ใช้ชื่อไฟล์เหล่านี้ตอนสั่งเทรน (dataset_object_name):")
        for name in object_names:
            print(f"   - {name}")

    except S3Error as e:
        print(f"❌ เกิดข้อผิดพลาดกับ MinIO: {e}")
        raise


if __name__ == "__main__":
    main()
