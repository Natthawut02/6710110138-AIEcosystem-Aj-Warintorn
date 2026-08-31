"""
Schemas สำหรับ Train Queue Endpoint (WTN-A07)
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TrainJobCreate(BaseModel):
    """
    ข้อมูลที่ Client ต้องส่งมาเพื่อขอเข้าคิวเทรนโมเดล
    """
    dataset_object_name: str = Field(
        ...,
        description="ชื่อไฟล์ dataset ที่เก็บอยู่ใน MinIO (bucket: datasets) เช่น 'conll2003/train.jsonl'",
        examples=["conll2003/train.jsonl"],
    )
    model_output_name: str = Field(
        ...,
        description="ชื่อโมเดลที่จะใช้ตั้งตอนบันทึกกลับไป MinIO เช่น 'token-classifier-v1'",
        examples=["token-classifier-v1"],
    )
    epochs: int = Field(default=1, ge=1, le=20, description="จำนวนรอบการเทรน")
    queue_time: Optional[datetime] = Field(
        default=None,
        description=(
            "เวลาที่ต้องการให้เริ่มเทรน (ISO 8601, เช่น 2026-09-01T22:00:00) "
            "ถ้าไม่ระบุ จะเริ่มเทรนทันทีที่ Trainer Worker ว่าง"
        ),
        examples=["2026-09-01T22:00:00"],
    )


class TrainJobInfo(BaseModel):
    """ข้อมูลตอบกลับหลัง enqueue งานเทรนสำเร็จ"""
    job_id: str
    status: str
    queue_name: str
    scheduled_start: Optional[datetime] = None
