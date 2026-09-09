"""
Schemas สำหรับ Prediction / Inference Endpoints (WTN-A08)
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class EntityInfo(BaseModel):
    """ข้อมูล Entity ที่ตรวจพบจากโมเดล Token Classification"""
    entity_group: str = Field(..., description="ประเภท Entity เช่น PER, ORG, LOC, MISC")
    score: float = Field(..., description="คะแนนความมั่นใจ (Confidence Score 0.0 - 1.0)")
    word: str = Field(..., description="คำหรือข้อความที่ตรงกับ Entity")
    start: int = Field(..., description="ดัชนีเริ่มต้นในข้อความ")
    end: int = Field(..., description="ดัชนีสิ้นสุดในข้อความ")


class PredictRequest(BaseModel):
    """ข้อมูลคำขอเพื่อส่งไปทำนายผล (Inference)"""
    text: str = Field(
        ...,
        description="ข้อความที่ต้องการวิเคราะห์ Named Entity Recognition (NER)",
        examples=["Barack Obama visited Google headquarters in California."]
    )
    model_name: Optional[str] = Field(
        default="ner_model",
        description="ชื่อ Model ใน MLflow Model Registry ที่ต้องการใช้งาน",
        examples=["ner_model"]
    )
    model_version: Optional[str] = Field(
        default="latest",
        description="เวอร์ชันของ Model ใน MLflow เช่น 'latest', '1', '2' หรือ Alias",
        examples=["latest"]
    )
    wait: bool = Field(
        default=True,
        description="ถ้าระบุ True ระบบจะรอผลลัพธ์จาก Inference Worker ทันที (Request/Response Synchronous) ถ้า False จะคืน job_id ทันที"
    )
    timeout: float = Field(
        default=10.0,
        ge=1.0,
        le=60.0,
        description="เวลารอผลลัพธ์สูงสุด (วินาที) ในกรณี wait=True"
    )


class PredictResponse(BaseModel):
    """ข้อมูลตอบกลับเมื่อประมวลผลการทำนายเสร็จสิ้น หรือคืน Job ID"""
    job_id: str
    status: str
    text: Optional[str] = None
    entities: Optional[List[Dict[str, Any]]] = None
    model_uri: Optional[str] = None
    latency_ms: Optional[float] = None
    message: Optional[str] = None


class JobStatusResponse(BaseModel):
    """ข้อมูลผลลัพธ์ของ Job ที่เรียกดูด้วย job_id"""
    job_id: str
    status: str
    result: Optional[Any] = None
    success: Optional[bool] = None
