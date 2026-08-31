"""
Train Queue Endpoint (WTN-A07: Trainer Worker Implementation)
รับคำขอเทรนโมเดลจาก Client แล้ว enqueue เข้าคิว ARQ เฉพาะสำหรับงานเทรน (training_queue)
เพื่อให้ Trainer Worker (container แยกที่มี GPU) เป็นตัวเดียวที่หยิบงานนี้ไปทำ
"""

from fastapi import APIRouter, HTTPException, status

from services.job_service import job_service
from schemas.train import TrainJobCreate, TrainJobInfo
from schemas.common import ErrorResponse

TRAINING_QUEUE_NAME = "training_queue"

router = APIRouter(prefix="/train", tags=["Trainer Worker"])


@router.post(
    "/enqueue",
    response_model=TrainJobInfo,
    status_code=status.HTTP_202_ACCEPTED,
    summary="เข้าคิวสั่งเทรนโมเดล (Token Classification)",
    description="""
รับคำสั่งเทรนโมเดล แล้ว enqueue งานเข้าคิว ARQ ชื่อ `training_queue` โดยเฉพาะ
เพื่อให้ Trainer Worker (container แยกที่มี GPU) เป็นตัวเดียวที่หยิบงานนี้ไปทำ

- **dataset_object_name**: ชื่อไฟล์ dataset ที่ต้องอัปโหลดเข้า MinIO ไว้ล่วงหน้าแล้ว
- **model_output_name**: ชื่อโมเดลที่จะใช้บันทึกกลับไป MinIO เมื่อเทรนเสร็จ
- **queue_time**: ถ้าระบุ งานจะไม่เริ่มจนกว่าจะถึงเวลานี้ (ใช้ ARQ `_defer_until` เบื้องหลัง)
    """,
    responses={
        202: {"description": "เข้าคิวสำเร็จ", "model": TrainJobInfo},
        500: {"description": "เข้าคิวไม่สำเร็จ (Redis connection error)", "model": ErrorResponse},
    },
)
async def enqueue_train_job(job_in: TrainJobCreate):
    try:
        job_info = await job_service.enqueue_job(
            job_name="train_token_classification",
            kwargs={
                "dataset_object_name": job_in.dataset_object_name,
                "model_output_name": job_in.model_output_name,
                "epochs": job_in.epochs,
            },
            defer_until=job_in.queue_time,
            queue_name=TRAINING_QUEUE_NAME,
        )
        return TrainJobInfo(
            job_id=job_info.job_id,
            status=job_info.status,
            queue_name=TRAINING_QUEUE_NAME,
            scheduled_start=job_in.queue_time,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ไม่สามารถเข้าคิวงานเทรนได้: {str(e)}",
        )


@router.get(
    "/{job_id}",
    summary="ตรวจสอบสถานะงานเทรน",
    description="ตรวจสอบว่างานเทรนที่ enqueue ไว้อยู่ในสถานะใด (queued / in_progress / complete)",
)
async def get_train_job_status(job_id: str):
    try:
        return await job_service.get_job_status(job_id=job_id, queue_name=TRAINING_QUEUE_NAME)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ตรวจสอบสถานะงาน {job_id} ไม่สำเร็จ: {str(e)}",
        )
